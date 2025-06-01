from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

class ExplanationAnalyzer:
    def __init__(self):
        self.model_id = "Qwen/Qwen3-4B"
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        print(f"Loading analyzer model {self.model_id} on {self.device}...")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_id)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_id,
                torch_dtype=torch.float16 if self.device.type == "cuda" else torch.float32,
                trust_remote_code=True
            )
            
            # Move model to device
            self.model = self.model.to(self.device)
            
            print(f"Analyzer model loaded successfully on {self.device}")
            print(f"Model device: {next(self.model.parameters()).device}")
            
        except Exception as e:
            print(f"Error loading analyzer model: {e}")
            raise
    
    def analyze_explanation(self, user_explanation, actual_red_flags, message_text):
        """Analyze user's explanation and assign points"""
        
        # Create a more natural prompt for conversational feedback
        prompt = f"""You are a cybersecurity instructor providing feedback to a student. The student was shown a text message and asked to identify if it's a scam and explain why.

The message was: "{message_text}"

The actual red flags in this message were: {', '.join(actual_red_flags)}

The student's explanation was: "{user_explanation}"

Provide natural, encouraging feedback as if you're talking to the student. Consider:
- What they identified correctly
- What important signs they might have missed
- How their reasoning was
- Any advice for spotting similar scams in the future

Give them a score of either 0, 10, 20 or 30 at the end of your feedback, depending on the quality of the response. Be conversational and educational, not robotic. Do not use any text styling. Keep your answers under 100 words."""

        messages = [
            {"role": "system", "content": "You are a friendly cybersecurity instructor who gives constructive feedback to students learning about online safety."},
            {"role": "user", "content": prompt}
        ]
        
        # Apply chat template
        text = self.tokenizer.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True,
            enable_thinking=False  # Disable thinking for efficiency
        )
        
        # Generate response
        model_inputs = self.tokenizer([text], return_tensors="pt")
        
        # Ensure inputs are on the same device as the model
        model_inputs = {k: v.to(self.device) for k, v in model_inputs.items()}
        
        with torch.no_grad():  # Save memory
            generated_ids = self.model.generate(
                **model_inputs,
                max_new_tokens=300,  # Increased for more natural response
                temperature=0.7,  # Higher temperature for more natural language
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
        
        output_ids = generated_ids[0][len(model_inputs['input_ids'][0]):].tolist()
        analysis = self.tokenizer.decode(output_ids, skip_special_tokens=True).strip()
        
        # Extract score and determine points
        score = self._extract_score(analysis)
        points = self._calculate_points(score)
        
        return {
            "analysis": analysis,
            "score": score,
            "points": points
        }
    
    def _extract_score(self, analysis_text):
        """Extract numerical score from analysis"""
        # Look for patterns like "score: 8" or "8/10" or just "8"
        import re
        
        # Try different patterns
        patterns = [
            r'score[:\s]+(\d+)',  # "score: 8"
            r'(\d+)/10',          # "8/10"
            r'(\d+)\s+out\s+of\s+10',  # "8 out of 10"
            r'\b([0-9]|10)\b'     # Just a number
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, analysis_text.lower())
            if matches:
                return int(matches[-1])  # Take the last match
        
        return 5  # Default middle score
    
    def _calculate_points(self, score):
        """Calculate points based on score"""
        if score >= 8:
            return 30  # Excellent explanation
        elif score >= 5:
            return 20  # Good explanation
        else:
            return 10  # Basic/poor explanation
        
    def analyze_web_content(self, element_text, element_html, user_reason, url, context):
        
        # Combine all available information
        full_content = f"Text: {element_text}\nURL: {url}\nUser reason: {user_reason}"
        
        # Check for common scam indicators
        scam_indicators = [
            'urgent', 'limited time', 'act now', 'click here', 'verify account',
            'suspended', 'unusual activity', 'confirm identity', 'prize', 'winner',
            'congratulations', 'free money', 'inheritance', 'lottery', 'tax refund'
        ]
        
        confidence = 0.0
        found_indicators = []
        
        content_lower = full_content.lower()
        for indicator in scam_indicators:
            if indicator in content_lower:
                confidence += 0.15
                found_indicators.append(indicator)
        
        # Check URL for suspicious patterns
        suspicious_domains = ['bit.ly', 'tinyurl', 'short.link', 't.co']
        if any(domain in url for domain in suspicious_domains):
            confidence += 0.2
            found_indicators.append('shortened URL')
        
        # Check HTML for suspicious attributes
        if 'onclick' in element_html.lower() or 'javascript:' in element_html.lower():
            confidence += 0.1
            found_indicators.append('suspicious JavaScript')
        
        # User reasoning weight
        if len(user_reason) > 20:  # Detailed explanation
            confidence += 0.1
        
        # Cap confidence at 1.0
        confidence = min(confidence, 1.0)
        
        is_likely_scam = confidence >= 0.5
        
        explanation = f"Analysis based on: {', '.join(found_indicators) if found_indicators else 'general content review'}"
        
        return {
            'is_likely_scam': is_likely_scam,
            'confidence': confidence,
            'explanation': explanation,
            'indicators_found': found_indicators
        }