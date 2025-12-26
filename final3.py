import numpy as np
import pandas as pd
import re
import torch
import joblib
import torch.nn as nn
from urllib.parse import urlparse, parse_qs

# --- LSTM Model Definition ---
class LSTMModel(nn.Module):
    def __init__(self, vocab_size, embed_dim=64, hidden_dim=128):
        super(LSTMModel, self).__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim)
        self.lstm = nn.LSTM(embed_dim, hidden_dim, batch_first=True, num_layers=2)
        self.dropout = nn.Dropout(0.5)
        self.fc = nn.Linear(hidden_dim, 2)
    
    def forward(self, x):
        x = self.embedding(x)
        x, _ = self.lstm(x)
        x = self.fc(x[:, -1, :])
        return x

# --- Main Phishing Detector Class ---
class PhishingDetector:
    def __init__(self, rf_model_path, lstm_model_path, vectorizer_path):
        # Load models
        self.rf_model = joblib.load(rf_model_path)
        self.vectorizer = joblib.load(vectorizer_path)
        self.vocab_size = len(self.vectorizer.get_feature_names_out()) + 1
        
        # Initialize LSTM
        self.lstm_model = LSTMModel(self.vocab_size)
        self.lstm_model.load_state_dict(torch.load(lstm_model_path))
        self.lstm_model.eval()
        
        # Homoglyph mappings (e.g., '0' → 'o')
        self.homoglyphs = {
            '0': ['o', 'O'],
            '1': ['l', 'i', 'I'],
            '2': ['z', 'Z'],
            '3': ['e', 'E'],
            '4': ['a', 'A'],
            '5': ['s', 'S'],
            '6': ['b', 'G'],
            '7': ['t', 'T'],
            '8': ['b', 'B'],
            '9': ['g', 'q']
        }
        
        # Allowed domains with numbers (e.g., 'zoom2u.com')
        self.allowed_domains = {'zoom2u.com', '4chan.org'}
    
    # --- UPI Validation ---
    def is_valid_upi_id(self, upi_id):
        """Check if a UPI ID follows name@provider format"""
        return re.match(r'^[a-zA-Z0-9._-]+@[a-zA-Z]+$', upi_id) is not None
    
    def is_valid_upi_url(self, url):
        """Validate UPI payment links (upi://pay?pa=...)"""
        if not url.startswith('upi://pay?'):
            return False
        
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            # Must have 'pa' (UPI ID)
            if 'pa' not in params:
                return False
            
            # Validate UPI ID
            upi_id = params['pa'][0]
            if not self.is_valid_upi_id(upi_id):
                return False
            
            return True
        except:
            return False
    
    # --- Homoglyph Detection ---
    def is_homoglyph_attack(self, domain):
        """Detect homoglyph substitutions like g00gle.com"""
        if domain in self.allowed_domains:
            return False
        
        # Skip UPI links
        if domain.startswith('upi://'):
            return False
        
        # Check for digit-to-letter substitutions
        for char in domain:
            if char.isdigit() and char in self.homoglyphs:
                return True
        
        # Check for suspicious patterns
        suspicious_patterns = [
            r'[0-9]+[a-z]',  # e.g., 'g00gle'
            r'[a-z]+[0-9]+', # e.g., 'go0gle123'
        ]
        
        return any(re.search(p, domain) for p in suspicious_patterns)
    
    # --- Text Processing ---
    def preprocess_domain(self, domain):
        """Extract main domain and handle UPI links"""
        if domain.startswith('upi://'):
            return 'valid_upi' if self.is_valid_upi_url(domain) else 'invalid_upi'
        return domain.split('.')[0].lower()
    
    def extract_bigrams(self, domain):
        """Convert domain to character bigrams"""
        if domain in ['valid_upi', 'invalid_upi']:
            return [domain]
        domain = re.sub(r'[^a-zA-Z0-9]', '', domain)
        return [domain[i:i+2] for i in range(len(domain)-1)]
    
    def text_to_sequence(self, text, max_len=20):
        """Convert text to numerical sequence for LSTM"""
        word_to_index = {word: idx + 1 for idx, word in enumerate(self.vectorizer.get_feature_names_out())}
        seq = [word_to_index.get(word, 0) for word in text.split()]
        return seq[:max_len] + [0] * (max_len - len(seq))
    
    # --- Main Detection Logic ---
    def detect_phishing(self, domains):
        """Analyze domains/URLs for phishing risk"""
        results = []
        
        for domain in domains:
            # Handle UPI URLs first
            if domain.startswith('upi://'):
                if self.is_valid_upi_url(domain):
                    results.append({
                        'domain': domain,
                        'is_phishing': False,
                        'reason': 'Valid UPI URL'
                    })
                else:
                    results.append({
                        'domain': domain,
                        'is_phishing': True,
                        'reason': 'Invalid UPI URL'
                    })
                continue
            
            # Check for homoglyph attacks
            if self.is_homoglyph_attack(domain):
                results.append({
                    'domain': domain,
                    'is_phishing': True,
                    'reason': 'Homoglyph attack detected'
                })
                continue
            
            # Default RF + LSTM analysis
            processed_domain = self.preprocess_domain(domain)
            bigrams = " ".join(self.extract_bigrams(processed_domain))
            
            # Random Forest prediction
            X_tfidf = self.vectorizer.transform([bigrams])
            rf_preds_prob = self.rf_model.predict_proba(X_tfidf)[:, 1]
            
            # LSTM prediction
            X_seq = np.array([self.text_to_sequence(bigrams)])
            X_tensor = torch.tensor(X_seq, dtype=torch.long)
            
            with torch.no_grad():
                lstm_outputs = self.lstm_model(X_tensor)
                lstm_preds_prob = torch.softmax(lstm_outputs, dim=1)[:, 1].numpy()
            
            # Ensemble prediction
            ensemble_prob = (rf_preds_prob + lstm_preds_prob) / 2
            results.append({
                'domain': domain,
                'rf_phishing_prob': rf_preds_prob[0],
                'lstm_phishing_prob': lstm_preds_prob[0],
                'ensemble_phishing_prob': ensemble_prob[0],
                'is_phishing': ensemble_prob[0] > 0.5,
                'reason': 'Suspicious domain' if ensemble_prob[0] > 0.5 else 'Likely safe'
            })
        
        return results

def test(url):
    detector = PhishingDetector(
        rf_model_path='random_forest_phishing_model1.joblib',
        lstm_model_path='lstm_phishing_model1.pth',
        vectorizer_path='tfidf_vectorizer1.joblib'
    )
    
    # Test cases
    test_domains = [url]
    
    # Run detection
    results = detector.detect_phishing(test_domains)
    
    # Print results
    print("Phishing Detection Results:")
    print("=" * 50)
    return results