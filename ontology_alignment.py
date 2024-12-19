from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL
import numpy as np
from difflib import SequenceMatcher
from textdistance import jaro_winkler, levenshtein, ratcliff_obershelp
from nltk.corpus import wordnet
import json
import os
import subprocess
import tempfile

class OntologyAligner:
    def __init__(self, confidence_threshold=0.7):
        self.confidence_threshold = confidence_threshold
        self.alignments_dir = "alignments"
        os.makedirs(self.alignments_dir, exist_ok=True)
        
    def load_ontology(self, rdf_content):
        """Load ontology from RDF content"""
        g = Graph()
        g.parse(data=rdf_content, format='xml')
        return g
        
    def get_concepts(self, graph):
        """Extract concepts (classes and properties) from the ontology"""
        concepts = []
        # Get all classes
        for s in graph.subjects(RDF.type, OWL.Class):
            label = str(graph.value(s, RDFS.label) or s).split('#')[-1]
            comment = str(graph.value(s, RDFS.comment) or '')
            concepts.append({
                'uri': str(s),
                'label': label,
                'comment': comment,
                'type': 'class'
            })
        # Get all properties
        for s in graph.subjects(RDF.type, OWL.DatatypeProperty):
            label = str(graph.value(s, RDFS.label) or s).split('#')[-1]
            comment = str(graph.value(s, RDFS.comment) or '')
            concepts.append({
                'uri': str(s),
                'label': label,
                'comment': comment,
                'type': 'property'
            })
        return concepts

    def string_similarity(self, str1, str2):
        """Enhanced string similarity measure combining multiple metrics"""
        # Convert strings to lowercase
        s1, s2 = str1.lower(), str2.lower()
        
        # Sequence matcher
        seq_sim = SequenceMatcher(None, s1, s2).ratio()
        
        # Jaro-Winkler similarity
        jw_sim = jaro_winkler.similarity(s1, s2)
        
        # Levenshtein similarity
        lev_sim = 1 - (levenshtein.distance(s1, s2) / max(len(s1), len(s2)))
        
        # Ratcliff-Obershelp similarity
        ro_sim = ratcliff_obershelp.similarity(s1, s2)
        
        # Semantic similarity using WordNet
        sem_sim = self.semantic_similarity(s1, s2)
        
        # Combine similarities with weights
        weights = [0.25, 0.25, 0.2, 0.2, 0.1]  # Adjust weights based on importance
        combined_sim = sum(w * s for w, s in zip(weights, [seq_sim, jw_sim, lev_sim, ro_sim, sem_sim]))
        
        return combined_sim

    def semantic_similarity(self, word1, word2):
        """Calculate semantic similarity using WordNet"""
        try:
            synsets1 = wordnet.synsets(word1)
            synsets2 = wordnet.synsets(word2)
            
            if not synsets1 or not synsets2:
                return 0.0
                
            max_sim = 0.0
            for syn1 in synsets1:
                for syn2 in synsets2:
                    sim = syn1.path_similarity(syn2) or 0.0
                    max_sim = max(max_sim, sim)
            
            return max_sim
        except:
            return 0.0

    def align_with_alignment_api(self, source_rdf, target_rdf):
        """Align ontologies using the Alignment API"""
        try:
            # Save ontologies to temporary files
            with tempfile.NamedTemporaryFile(suffix='.rdf', delete=False) as source_file:
                source_file.write(source_rdf.encode())
                source_path = source_file.name
                
            with tempfile.NamedTemporaryFile(suffix='.rdf', delete=False) as target_file:
                target_file.write(target_rdf.encode())
                target_path = target_file.name
            
            # Run Alignment API (assuming it's installed and in PATH)
            cmd = [
                'java', '-jar', 'align.jar',
                '-i', source_path,
                '-o', target_path,
                '--format', 'json'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                alignments = json.loads(result.stdout)
                return self.convert_alignment_api_results(alignments)
            else:
                return []
                
        except Exception as e:
            print(f"Error using Alignment API: {str(e)}")
            return []
        finally:
            # Clean up temporary files
            if 'source_path' in locals(): os.unlink(source_path)
            if 'target_path' in locals(): os.unlink(target_path)

    def convert_alignment_api_results(self, api_alignments):
        """Convert Alignment API results to our format"""
        alignments = []
        for a in api_alignments:
            alignments.append({
                'source_uri': a['entity1'],
                'target_uri': a['entity2'],
                'confidence': float(a['measure']),
                'type': a.get('type', 'unknown'),
                'needs_confirmation': float(a['measure']) < self.confidence_threshold
            })
        return alignments

    def align_ontologies(self, source_rdf, target_rdf, method='combined'):
        """Align two ontologies using specified method"""
        if method == 'api':
            return self.align_with_alignment_api(source_rdf, target_rdf)
        elif method == 'custom':
            return self.align_ontologies_custom(source_rdf, target_rdf)
        else:  # combined
            api_alignments = self.align_with_alignment_api(source_rdf, target_rdf)
            custom_alignments = self.align_ontologies_custom(source_rdf, target_rdf)
            return self.merge_alignments(api_alignments, custom_alignments)

    def align_ontologies_custom(self, source_rdf, target_rdf):
        """Custom alignment method"""
        source_graph = self.load_ontology(source_rdf)
        target_graph = self.load_ontology(target_rdf)
        
        source_concepts = self.get_concepts(source_graph)
        target_concepts = self.get_concepts(target_graph)
        
        alignments = []
        
        for source in source_concepts:
            best_matches = []
            
            for target in target_concepts:
                if source['type'] != target['type']:
                    continue
                    
                # Calculate string similarity
                label_sim = self.string_similarity(source['label'], target['label'])
                
                # Calculate comment similarity if available
                comment_sim = 0.0
                if source['comment'] and target['comment']:
                    comment_sim = self.string_similarity(source['comment'], target['comment'])
                
                # Combined similarity score
                similarity = 0.7 * label_sim + 0.3 * comment_sim
                
                if similarity > 0.5:  # Minimum threshold
                    best_matches.append({
                        'target': target,
                        'score': similarity
                    })
            
            # Sort matches by score
            best_matches.sort(key=lambda x: x['score'], reverse=True)
            
            # Take top matches
            for match in best_matches[:3]:  # Consider top 3 matches
                alignments.append({
                    'source_uri': source['uri'],
                    'target_uri': match['target']['uri'],
                    'confidence': match['score'],
                    'type': source['type'],
                    'needs_confirmation': match['score'] < self.confidence_threshold
                })
        
        return alignments

    def merge_alignments(self, alignments1, alignments2):
        """Merge alignments from different methods"""
        merged = {}
        
        # Process first set of alignments
        for a in alignments1:
            key = (a['source_uri'], a['target_uri'])
            merged[key] = a
        
        # Process second set, updating confidence if better
        for a in alignments2:
            key = (a['source_uri'], a['target_uri'])
            if key in merged:
                if a['confidence'] > merged[key]['confidence']:
                    merged[key] = a
            else:
                merged[key] = a
        
        return list(merged.values())

    def save_alignment(self, service_id, alignments):
        """Save alignment to a file"""
        filename = os.path.join(self.alignments_dir, f"alignment_{service_id}.json")
        with open(filename, 'w') as f:
            json.dump(alignments, f, indent=2)

    def load_alignment(self, service_id):
        """Load alignment from file"""
        filename = os.path.join(self.alignments_dir, f"alignment_{service_id}.json")
        try:
            with open(filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return None

    def transform_data(self, data, alignments):
        """Transform data using the alignment mappings"""
        transformed = {}
        for key, value in data.items():
            # Find corresponding mapping
            mapping = next((m for m in alignments if m['source_uri'].endswith(key)), None)
            if mapping:
                new_key = mapping['target_uri'].split('#')[-1]
                transformed[new_key] = value
            else:
                transformed[key] = value
        return transformed