import React, { useState, useCallback } from 'react';
import { Upload, Play, Download, Sparkles, Clock, CreditCard } from 'lucide-react';
import { Toaster, toast } from 'react-hot-toast';
import axios from 'axios';

// API Configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8093';

// Video duration options
const DURATION_OPTIONS = [
  { value: 5, label: '5 seconds', price: '€4.90' },
  { value: 10, label: '10 seconds', price: '€6.90' },
  { value: 20, label: '20 seconds', price: '€9.90' },
  { value: 30, label: '30 seconds', price: '€14.90' },
  { value: 60, label: '60 seconds', price: '€24.90' },
];

function App() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [duration, setDuration] = useState(20);
  const [isUploading, setIsUploading] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [videoUrl, setVideoUrl] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);

  // Handle file selection
  const handleFileSelect = useCallback((file: File) => {
    if (file.size > 10 * 1024 * 1024) {
      toast.error('File size must be less than 10MB');
      return;
    }

    if (!file.type.startsWith('image/')) {
      toast.error('Please select an image file');
      return;
    }

    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    toast.success('Image selected successfully!');
  }, []);

  // Handle file drop
  const handleDrop = useCallback((e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFileSelect(file);
    }
  }, [handleFileSelect]);

  // Handle file input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFileSelect(file);
    }
  };

  // Start the generation process
  const handleGenerate = async () => {
    if (!selectedFile) {
      toast.error('Please select an image first');
      return;
    }

    try {
      setIsUploading(true);
      toast.loading('Uploading your image...');

      // 1. Initialize upload
      const initResponse = await axios.post(`${API_URL}/api/upload/init`, {
        filename: selectedFile.name,
      });

      const uploadUrl = initResponse.data.uploadUrl;

      // 2. Upload file
      const formData = new FormData();
      formData.append('file', selectedFile);

      await axios.post(uploadUrl, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      toast.dismiss();
      toast.success('Image uploaded successfully!');
      setIsUploading(false);

      // 3. Create checkout session
      toast.loading('Preparing payment...');

      const sessionResponse = await axios.post(`${API_URL}/api/checkout/session`, {
        jobId: initResponse.data.uploadId,
        duration,
        email: 'demo@example.com',
        locale: 'en',
      });

      toast.dismiss();

      // 4. In production, redirect to Stripe
      // For demo, simulate successful payment
      toast.success('Payment simulation successful!');
      setJobId(sessionResponse.data.jobId);
      setIsProcessing(true);

      // 5. Simulate video processing
      simulateProcessing();

    } catch (error) {
      toast.dismiss();
      toast.error('An error occurred. Please try again.');
      console.error(error);
      setIsUploading(false);
    }
  };

  // Simulate video processing progress
  const simulateProcessing = () => {
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsProcessing(false);
          setVideoUrl('https://storage.googleapis.com/demo-bucket/sample-video.mp4');
          toast.success('Video generated successfully!');
          return 100;
        }
        return prev + 10;
      });
    }, 1000);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-white to-blue-50">
      <Toaster position="top-right" />

      {/* Header */}
      <header className="px-6 py-4 border-b bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Sparkles className="w-8 h-8 text-purple-600" />
            <h1 className="text-2xl font-bold bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              AnimateMyPicture
            </h1>
          </div>
          <a
            href="https://github.com/yourusername/AnimateMyPicture-Public"
            target="_blank"
            rel="noopener noreferrer"
            className="text-gray-600 hover:text-gray-900"
          >
            GitHub
          </a>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-12">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-bold mb-4">
            Transform Your Photos into{' '}
            <span className="bg-gradient-to-r from-purple-600 to-blue-600 bg-clip-text text-transparent">
              Living Memories
            </span>
          </h2>
          <p className="text-lg text-gray-600">
            Upload an image and watch AI bring it to life with stunning animations
          </p>
        </div>

        {/* Upload Section */}
        {!videoUrl && (
          <div className="bg-white rounded-2xl shadow-xl p-8 mb-8">
            {/* File Upload Area */}
            {!selectedFile ? (
              <div
                onDrop={handleDrop}
                onDragOver={(e) => e.preventDefault()}
                className="border-3 border-dashed border-gray-300 rounded-xl p-12 text-center hover:border-purple-500 transition-colors cursor-pointer"
              >
                <Upload className="w-16 h-16 text-gray-400 mx-auto mb-4" />
                <p className="text-xl mb-2">Drop your image here</p>
                <p className="text-gray-500 mb-4">or</p>
                <label className="inline-block">
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleInputChange}
                    className="hidden"
                  />
                  <span className="px-6 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 cursor-pointer transition-colors">
                    Browse Files
                  </span>
                </label>
                <p className="text-sm text-gray-500 mt-4">
                  Supports JPG, PNG, WebP (max 10MB)
                </p>
              </div>
            ) : (
              <div className="space-y-6">
                {/* Image Preview */}
                <div className="relative rounded-xl overflow-hidden">
                  <img
                    src={previewUrl}
                    alt="Preview"
                    className="w-full max-h-96 object-contain"
                  />
                  <button
                    onClick={() => {
                      setSelectedFile(null);
                      setPreviewUrl('');
                    }}
                    className="absolute top-4 right-4 px-3 py-1 bg-red-500 text-white rounded-lg hover:bg-red-600"
                  >
                    Remove
                  </button>
                </div>

                {/* Duration Selection */}
                <div>
                  <label className="block text-sm font-medium mb-2">
                    Video Duration
                  </label>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {DURATION_OPTIONS.map((option) => (
                      <button
                        key={option.value}
                        onClick={() => setDuration(option.value)}
                        className={`p-3 rounded-lg border-2 transition-all ${
                          duration === option.value
                            ? 'border-purple-600 bg-purple-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-medium">{option.label}</span>
                          <Clock className="w-4 h-4 text-gray-500" />
                        </div>
                        <div className="text-sm text-purple-600 font-semibold mt-1">
                          {option.price}
                        </div>
                      </button>
                    ))}
                  </div>
                </div>

                {/* Generate Button */}
                <button
                  onClick={handleGenerate}
                  disabled={isUploading || isProcessing}
                  className="w-full py-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-xl font-semibold hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center space-x-2"
                >
                  {isUploading ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                      <span>Uploading...</span>
                    </>
                  ) : isProcessing ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-2 border-white border-t-transparent" />
                      <span>Processing... {progress}%</span>
                    </>
                  ) : (
                    <>
                      <CreditCard className="w-5 h-5" />
                      <span>Generate Video - {DURATION_OPTIONS.find(d => d.value === duration)?.price}</span>
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Progress Bar */}
        {isProcessing && (
          <div className="bg-white rounded-xl shadow-lg p-6 mb-8">
            <div className="flex items-center justify-between mb-4">
              <span className="text-sm font-medium">Generating your video...</span>
              <span className="text-sm text-gray-500">{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-gradient-to-r from-purple-600 to-blue-600 h-2 rounded-full transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="text-xs text-gray-500 mt-2">
              AI is analyzing and animating your image...
            </p>
          </div>
        )}

        {/* Video Result */}
        {videoUrl && (
          <div className="bg-white rounded-2xl shadow-xl p-8">
            <h3 className="text-2xl font-bold mb-4 text-center">
              🎉 Your Video is Ready!
            </h3>
            <div className="rounded-xl overflow-hidden mb-6">
              <video
                src={videoUrl}
                controls
                autoPlay
                loop
                className="w-full"
              />
            </div>
            <div className="flex gap-4">
              <button
                onClick={() => window.open(videoUrl, '_blank')}
                className="flex-1 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center justify-center space-x-2"
              >
                <Download className="w-5 h-5" />
                <span>Download Video</span>
              </button>
              <button
                onClick={() => {
                  setVideoUrl(null);
                  setSelectedFile(null);
                  setPreviewUrl('');
                  setProgress(0);
                }}
                className="flex-1 py-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors flex items-center justify-center space-x-2"
              >
                <Play className="w-5 h-5" />
                <span>Create Another</span>
              </button>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-20 py-8 border-t bg-white/80 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-6 text-center text-gray-600">
          <p>Built with ❤️ using cutting-edge AI technology</p>
          <p className="mt-2 text-sm">
            © 2024 AnimateMyPicture |
            <a href="#" className="ml-1 hover:text-purple-600">Privacy</a> |
            <a href="#" className="ml-1 hover:text-purple-600">Terms</a>
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;