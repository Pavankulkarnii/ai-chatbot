# AI Chatbot v2.0 - With Next-Word Prediction

A ChatGPT-like chatbot with intelligent next-word predictions, powered by GPT-2 and optimized for Apple Silicon (M4).

## ✨ Features

- 💬 **Smart Conversations**: Powered by GPT-2 medium model
- 🔮 **Next-Word Prediction**: Real-time autocomplete suggestions
- ⚡ **MPS Accelerated**: Uses Apple Silicon GPU for faster inference
- 💾 **Response Caching**: Caches responses for improved performance
- 🔌 **WebSocket Support**: Real-time chat with typing indicators
- 🎨 **Modern UI**: Clean, responsive interface with dark theme

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/Pavankulkarnii/ai-chatbot.git
cd ai-chatbot
```

### 2. Install Dependencies
```bash
# Create virtual environment
python3 -m venv venv

# Activate it (macOS/Linux)
source venv/bin/activate

# Install packages
pip install -r backend/requirements.txt
```

### 3. Run Backend Server
```bash
cd backend
python main.py
```

Wait for the message: `Model will be loaded on first request (lazy loading)`

The model will automatically load when you send your first message.

### 4. Run Frontend (New Terminal)
```bash
cd frontend
python3 -m http.server 3000
```

### 5. Open Browser

Go to: **http://localhost:3000**

## 🎯 Usage

### Chat
- Type your message in the input box
- Press Enter or click Send
- Wait for AI response

### Next-Word Prediction
- Start typing (minimum 3 characters)
- Autocomplete suggestions appear above input
- Click any suggestion to insert it
- Predictions show probability scores

### Controls
- **Reset**: Clear conversation history
- **Clear Cache**: Clear response cache

## 📡 API Endpoints

### Chat
```bash
POST /api/chat
Body: {"message": "Hello", "temperature": 0.7, "max_length": 1000}
```

### Next-Word Prediction
```bash
POST /api/predict
Body: {"text": "Hello how are", "num_predictions": 3, "temperature": 0.8}
```

### Reset Conversation
```bash
POST /api/reset
```

### Clear Cache
```bash
POST /api/clear-cache
```

### Model Info
```bash
GET /api/info
```

### WebSocket
```
ws://localhost:8000/ws/chat
```

## 🔧 Configuration

Edit `backend/chat_model.py` to change model:
```python
# Options:
# - "gpt2-medium" (355M params) - Default, good balance
# - "gpt2-large" (774M params) - Better quality
# - "meta-llama/Llama-3.2-1B-Instruct" - Best quality
```

## 📊 Performance

- **First request**: 20-30 seconds (model loading)
- **Subsequent requests**: 1-3 seconds per response
- **Next-word prediction**: <500ms
- **Memory usage**: ~2-3GB RAM with gpt2-medium
- **Device**: Automatically uses MPS (Apple Silicon GPU)

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.8+

# Reinstall dependencies
pip install --upgrade -r backend/requirements.txt
```

### Model loading fails
```bash
# Clear model cache and retry
rm -rf backend/models/
```

### MPS not available
```bash
# Check PyTorch MPS support
python -c "import torch; print(torch.backends.mps.is_available())"
```

### CORS errors
The backend allows all origins (`allow_origins=["*"]`). 
For production, update `backend/main.py`:
```python
allow_origins=["http://localhost:3000"]
```

## 📁 Project Structure
```
ai-chatbot/
├── backend/
│   ├── main.py              # FastAPI server
│   ├── chat_model.py        # Model handler (NEW)
│   └── requirements.txt     # Dependencies
├── frontend/
│   ├── index.html           # UI (UPDATED)
│   └── app.js               # Logic (UPDATED)
├── .gitignore               # Ignore large files
└── README.md                # This file
```

## 🔄 Updates in v2.0

- ✅ Added next-word prediction endpoint
- ✅ Upgraded to GPT-2 for better responses
- ✅ Implemented response caching
- ✅ Lazy model loading for faster startup
- ✅ Shared model instance across endpoints
- ✅ Live autocomplete in frontend
- ✅ Probability scores for predictions
- ✅ MPS (Apple Silicon) optimization

## 📝 License

MIT License

## 🤝 Contributing

Pull requests welcome! For major changes, please open an issue first.

## 📧 Contact

GitHub: [@Pavankulkarnii](https://github.com/Pavankulkarnii)
