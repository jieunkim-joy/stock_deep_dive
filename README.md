# 📈 Stock Deep-Dive AI

A comprehensive stock analysis dashboard powered by AI, providing deep financial insights, technical analysis, and investment recommendations.

## ✨ Features

### Core Functionality
- **Comprehensive Data Collection**: Real-time stock data, financial statements (annual & quarterly), and news sentiment
- **AI-Powered Analysis**: Google Gemini AI integration for macro-economic analysis, forensic accounting, and investment strategy recommendations
- **Financial Forensic Analysis**: Quality of earnings, turnover ratios, interest coverage, CapEx growth, and buyback yield
- **Technical Analysis**: RSI, TRIX, moving averages, and volume analysis with interactive charts
- **Trend Analysis**: Annual and quarterly trend visualization for all derived financial metrics
- **Raw Data Viewer**: Complete access to all collected raw data with CSV/JSON export capabilities

### Investment Strategies
- **Growth Strategy**: Focus on revenue growth, CapEx expansion, market share potential
- **Value Strategy**: Emphasis on FCF generation, dividends, buybacks, and debt reduction

### User Experience
- **Flexible API Key Management**: Works with or without API key (shows basic indicators without AI analysis)
- **Bilingual Support**: English and Korean interface
- **Interactive Visualizations**: Plotly charts with candlestick, line, bar, and radar charts

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
```bash
git clone git@github.com:jieunkim-joy/stock_deep_dive.git
cd stock_deep_dive
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Run the application**
```bash
streamlit run app.py
```

4. **Access the dashboard**
   - Open your browser and navigate to `http://localhost:8501`
   - Enter a ticker symbol (e.g., AAPL, NVDA, GOOGL)
   - Optionally enter your Gemini API key for AI analysis
   - Click "Run Analysis"

## ☁️ Streamlit Community Cloud Deployment

### Prerequisites
- GitHub account
- Streamlit Community Cloud account ([sign up here](https://streamlit.io/cloud))
- Google Gemini API key (optional, for AI features)

### Deployment Steps

1. **Push code to GitHub**
   ```bash
   git add .
   git commit -m "Prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [Streamlit Community Cloud](https://share.streamlit.io/)
   - Click "New app"
   - Connect your GitHub repository
   - Select repository: `jieunkim-joy/stock_deep_dive`
   - Branch: `main`
   - Main file path: `app.py`
   - Click "Deploy"

3. **Configure Secrets (Optional - for AI features)**
   - In your Streamlit Cloud app settings, go to "Secrets"
   - Add the following:
   ```toml
   GEMINI_API_KEY = "your-gemini-api-key-here"
   ```
   - Save and the app will automatically redeploy

### Configuration Files

- **`.streamlit/config.toml`**: Streamlit configuration (theme, server settings)
- **`requirements.txt`**: Python dependencies
- **`.gitignore`**: Git ignore patterns

## 📋 Requirements

### Python Version
- Python 3.8 or higher

### Key Dependencies
- `streamlit>=1.28.0`: Web framework
- `yfinance>=0.2.28`: Stock data collection
- `pandas>=2.0.0`: Data manipulation
- `plotly>=5.17.0`: Interactive visualizations
- `google-generativeai>=0.3.0`: Gemini AI integration
- `pandas-ta>=0.3.14b0`: Technical indicators
- `numpy>=1.24.0`: Numerical computations

See `requirements.txt` for complete list.

## 📁 Project Structure

```
stock_deep_dive/
├── app.py                      # Main Streamlit application (entry point)
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .streamlit/
│   └── config.toml            # Streamlit configuration
├── .gitignore                 # Git ignore patterns
├── stock/                     # Core application modules
│   ├── data_manager.py        # Data collection and processing
│   ├── ai_analyst.py          # AI analysis engine
│   └── utils.py               # Utility functions
├── ARCHITECTURE_ANALYSIS.md   # Architecture documentation
├── REFACTORING_SUMMARY.md     # Refactoring documentation
└── archive/                   # Archived files and tests
```

## 🔑 API Key Setup

### Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the API key

### Using the API Key

**Manual Input (Required)**
- Enter the API key in the sidebar when using the app
- The key is entered manually each session and is **never stored or hardcoded**
- The key is only used during the current session and is cleared when the app refreshes

**Security Note**: 
- API keys are never stored in code, environment variables, or secrets
- Users must enter their own API key each time they use AI features
- The app works without an API key, but AI analysis features will be disabled. Basic financial indicators and charts will still be available.

## 🎯 Usage Guide

### Basic Workflow

1. **Enter Ticker**: Type a stock ticker symbol (e.g., AAPL, MSFT, TSLA)
2. **Select Strategy**: Choose Growth or Value investment style
3. **Choose Language**: Select English or Korean
4. **Enter API Key** (optional): For AI-powered analysis
5. **Run Analysis**: Click the "Run Analysis" button
6. **Explore Results**: Navigate through 5 tabs:
   - Executive Summary: AI analysis and radar chart
   - Macro & Industry: Macroeconomic context and industry analysis
   - Financials: Forensic checks and financial charts
   - Technicals: Price charts, indicators, and news
   - Raw Data: Complete raw data access

### Understanding the Analysis

- **AI Score (0-100)**: Overall investment attractiveness score
- **Verdict**: STRONG BUY / BUY / HOLD / SELL recommendation
- **Forensic Metrics**: Quality of earnings, turnover ratios, interest coverage
- **Technical Indicators**: RSI, TRIX, moving averages, volume analysis
- **Trend Charts**: Visual representation of financial metrics over time

## 🛠️ Development

### Running Tests

```bash
# Navigate to archive/test_files for test scripts
cd archive/test_files
python test_data_manager.py
python test_ai_analyst.py
```

### Code Quality

- Follows SOLID principles
- Clean Architecture structure
- Comprehensive error handling
- DRY (Don't Repeat Yourself) principles

### Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📊 Data Sources

- **Market Data**: Yahoo Finance (via yfinance)
- **AI Analysis**: Google Gemini API
- **News**: Yahoo Finance news feed

## ⚠️ Limitations

- Quarterly financial data may not be available for all tickers (yfinance limitation)
- API rate limits apply for Gemini API
- Free tier has usage restrictions

## 📝 License

This project is open source and available for personal and educational use.

## 🤝 Support

For issues, questions, or contributions, please open an issue on GitHub.

## 📈 Version History

- **v1.2**: Code refactoring, raw data viewer, trend analysis features
- **v1.0**: Initial MVP release

---

**Built with ❤️ using Streamlit and Python**

