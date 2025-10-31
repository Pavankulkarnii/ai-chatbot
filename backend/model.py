import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatbotModel:
    def __init__(self, model_name="microsoft/DialoGPT-medium", cache_dir="./models"):
        """
        Initialize chatbot model optimized for Apple Silicon M4
        
        Model options:
        - microsoft/DialoGPT-medium (345M - Recommended for 8GB RAM)
        - microsoft/DialoGPT-large (774M - For 16GB+ RAM)
        - gpt2-medium (355M)
        - gpt2-large (774M)
        """
        logger.info(f"Loading model: {model_name}")
        
        # Check device availability (MPS for Apple Silicon)
        if torch.backends.mps.is_available():
            self.device = torch.device("mps")
            logger.info("✅ Using Apple Silicon GPU (MPS) for acceleration")
        else:
            self.device = torch.device("cpu")
            logger.info("⚠️  MPS not available, using CPU")
        
        # Create cache directory
        Path(cache_dir).mkdir(exist_ok=True)
        
        # Load tokenizer
        logger.info("Loading tokenizer...")
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            cache_dir=cache_dir
        )
        
        # Load model
        logger.info("Loading model (this may take a minute)...")
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            cache_dir=cache_dir,
            torch_dtype=torch.float32  # Use float32 for MPS compatibility
        )
        
        # Move model to device (MPS/CPU)
        self.model.to(self.device)
        self.model.eval()
        
        # Set pad token
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
        
        self.chat_history_ids = None
        logger.info("✅ Model loaded successfully!")
        logger.info(f"Model size: {sum(p.numel() for p in self.model.parameters()) / 1e6:.1f}M parameters")
    
    def generate_response(self, user_input, max_length=1000, temperature=0.7, top_k=50, top_p=0.95):
        """
        Generate chatbot response with MPS acceleration
        """
        try:
            # Encode user input
            new_input_ids = self.tokenizer.encode(
                user_input + self.tokenizer.eos_token,
                return_tensors='pt'
            ).to(self.device)
            
            # Append to chat history
            if self.chat_history_ids is not None:
                bot_input_ids = torch.cat([self.chat_history_ids, new_input_ids], dim=-1)
            else:
                bot_input_ids = new_input_ids
            
            # Limit context length to prevent memory issues
            if bot_input_ids.shape[-1] > 800:
                bot_input_ids = bot_input_ids[:, -800:]
            
            # Generate response
            with torch.no_grad():  # Disable gradient calculation for inference
                self.chat_history_ids = self.model.generate(
                    bot_input_ids,
                    max_length=max_length,
                    pad_token_id=self.tokenizer.pad_token_id,
                    temperature=temperature,
                    do_sample=True,
                    top_k=top_k,
                    top_p=top_p,
                    no_repeat_ngram_size=3,
                    repetition_penalty=1.2
                )
            
            # Decode response
            response = self.tokenizer.decode(
                self.chat_history_ids[:, bot_input_ids.shape[-1]:][0],
                skip_special_tokens=True
            )
            
            return response.strip() if response else "I'm not sure how to respond to that."
        
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "Sorry, I encountered an error. Please try again."
    
    def reset_history(self):
        """Reset conversation history"""
        self.chat_history_ids = None
        logger.info("Conversation history reset")

# Global model instance
chatbot = None

def get_chatbot():
    """Get or create chatbot instance (singleton pattern)"""
    global chatbot
    if chatbot is None:
        chatbot = ChatbotModel()
    return chatbot

def test_model():
    """Test model loading and inference"""
    logger.info("Testing model...")
    bot = get_chatbot()
    
    test_messages = [
        "Hello! How are you?",
        "What can you help me with?",
        "Tell me a joke"
    ]
    
    for msg in test_messages:
        logger.info(f"User: {msg}")
        response = bot.generate_response(msg)
        logger.info(f"Bot: {response}\n")
    
    bot.reset_history()
    logger.info("✅ Model test complete!")

if __name__ == "__main__":
    test_model()
    
    
