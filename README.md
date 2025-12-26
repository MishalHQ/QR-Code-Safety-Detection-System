# 🔒 QR Code Safety Detection System

A comprehensive security tool that scans QR codes from images and analyzes the embedded URLs for potential threats using multiple security APIs and local blacklist checking.

## 🎯 Overview

This Flask-based web application provides real-time QR code scanning and URL safety analysis. It combines computer vision techniques with multiple security APIs to detect malicious URLs, phishing attempts, and other security threats embedded in QR codes.

## ✨ Features

- **QR Code Detection**: Automatically detects and decodes QR codes from uploaded images
- **Multi-Layer Security Analysis**:
  - Local blacklist checking for immediate threat detection
  - VirusTotal API integration for comprehensive malware scanning
  - Google Safe Browsing API for phishing and malware detection
- **Real-time Processing**: Fast image processing and URL analysis
- **User-Friendly Interface**: Clean web interface for easy QR code scanning
- **Detailed Reports**: Comprehensive security reports with threat details
- **Multiple Format Support**: Supports PNG, JPG, JPEG, and GIF images

## 🛠️ Technologies Used

- **Backend**: Flask (Python web framework)
- **Computer Vision**: OpenCV, pyzbar
- **Security APIs**: VirusTotal, Google Safe Browsing
- **Image Processing**: NumPy, OpenCV
- **Environment Management**: python-dotenv

## 📦 Installation

### Prerequisites

- Python 3.7 or higher
- pip package manager
- API Keys (optional but recommended):
  - VirusTotal API Key
  - Google Safe Browsing API Key

### Setup

1. **Clone the repository**
```bash
git clone https://github.com/MishalHQ/QR-Code-Safety-Detection-System.git
cd QR-Code-Safety-Detection-System
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables**

Create a `.env` file in the project root:
```env
VIRUSTOTAL_API_KEY=your_virustotal_api_key_here
GOOGLE_SAFE_BROWSING_API_KEY=your_google_safe_browsing_api_key_here
```

**Get API Keys:**
- VirusTotal: https://www.virustotal.com/gui/join-us
- Google Safe Browsing: https://developers.google.com/safe-browsing/v4/get-started

4. **Create uploads directory** (if not exists)
```bash
mkdir uploads
```

## 🚀 Usage

### Running the Application

```bash
python app.py
```

The application will start on `http://localhost:5000`

### Using the Web Interface

1. Open your browser and navigate to `http://localhost:5000`
2. Upload an image containing a QR code
3. Click "Scan QR Code"
4. View the security analysis results

### API Endpoint

**POST /scan**
- Upload an image file
- Returns JSON with QR code data and security analysis

Example using curl:
```bash
curl -X POST -F "file=@qrcode.png" http://localhost:5000/scan
```

## 📁 Project Structure

```
QR-Code-Safety-Detection-System/
├── app.py                    # Main Flask application
├── final3.py                 # Additional processing module
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables (not tracked)
├── static/                   # Static files
│   ├── css/
│   │   └── styles.css       # Stylesheet
│   └── js/
│       └── script.js        # JavaScript functionality
├── templates/                # HTML templates
│   └── index.html           # Main web interface
└── uploads/                  # Uploaded images directory
```

## 🔍 How It Works

1. **Image Upload**: User uploads an image containing a QR code
2. **QR Detection**: OpenCV and pyzbar decode the QR code
3. **URL Extraction**: System extracts the embedded URL
4. **Security Analysis**:
   - Checks against local blacklist
   - Queries VirusTotal for malware detection
   - Queries Google Safe Browsing for phishing detection
5. **Report Generation**: Comprehensive security report is generated
6. **Result Display**: User receives detailed safety analysis

## 🛡️ Security Features

### Local Blacklist
Immediate detection of known malicious domains without API calls.

### VirusTotal Integration
- Scans URLs against 70+ antivirus engines
- Provides detailed malware analysis
- Historical threat data

### Google Safe Browsing
- Detects phishing sites
- Identifies malware distribution
- Social engineering detection

## 📊 Dependencies

Key dependencies (see `requirements.txt` for complete list):
- Flask 3.1.1 - Web framework
- OpenCV 4.12.0 - Image processing
- pyzbar 0.1.9 - QR code decoding
- requests 2.32.4 - API communication
- python-dotenv 1.1.1 - Environment management
- numpy 2.2.6 - Numerical computing

## ⚙️ Configuration

### Upload Settings
- Maximum file size: 5MB
- Allowed formats: PNG, JPG, JPEG, GIF

### API Rate Limits
- VirusTotal: 4 requests/minute (free tier)
- Google Safe Browsing: 10,000 requests/day (free tier)

## 🔐 Security Best Practices

1. **Never commit API keys** - Use `.env` file
2. **Validate all inputs** - File type and size checking
3. **Sanitize filenames** - Using secure_filename
4. **Regular updates** - Keep dependencies updated
5. **HTTPS in production** - Use SSL certificates

## 🚨 Error Handling

The system handles:
- Invalid image formats
- Corrupted QR codes
- API failures
- Network timeouts
- Missing API keys

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📝 License

This project is open source and available under the MIT License.

## 👨‍💻 Author

**Mohammed Mishal**
- GitHub: [@MishalHQ](https://github.com/MishalHQ)

## 🙏 Acknowledgments

- OpenCV community for computer vision tools
- pyzbar for QR code decoding
- VirusTotal and Google Safe Browsing for security APIs

## 📞 Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

⭐ If you find this project useful, please consider giving it a star!

## 🔮 Future Enhancements

- [ ] Batch QR code processing
- [ ] Real-time camera scanning
- [ ] Mobile app integration
- [ ] Custom blacklist management
- [ ] Historical scan database
- [ ] Email notifications for threats
- [ ] PDF report generation