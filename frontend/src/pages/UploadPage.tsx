import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Upload, Mic } from "lucide-react";
import { useDropzone } from "react-dropzone";
import { api } from "../api/client";
import { useConfigStore } from "../stores/configStore";
import AudioRecorder from "../components/AudioRecorder";

type InputMode = "upload" | "record";

export default function UploadPage() {
	const navigate = useNavigate();
	const [isUploading, setIsUploading] = useState(false);
	const [error, setError] = useState<string | null>(null);
	const [inputMode, setInputMode] = useState<InputMode>("upload");
	const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);

	const { theme, includeImages, interactiveMode, saveTranscription, setTheme, toggleImages, toggleInteractive, toggleSaveTranscription } =
		useConfigStore();

	const onDrop = async (acceptedFiles: File[]) => {
		if (acceptedFiles.length === 0) return;

		const file = acceptedFiles[0];
		setError(null);
		setIsUploading(true);

		try {
			const response = await api.generatePresentation(file, {
				theme,
				includeImages,
				interactiveMode,
				saveTranscription,
			});

			navigate(`/job/${response.job_id}`);
		} catch (err: any) {
			const detail = err.response?.data?.detail;
			// Handle both string and object error formats
			const errorMessage = typeof detail === 'string'
				? detail
				: detail?.message || detail?.error || "Failed to upload file";
			setError(errorMessage);
		} finally {
			setIsUploading(false);
		}
	};

	const { getRootProps, getInputProps, isDragActive } = useDropzone({
		onDrop,
		accept: {
			"audio/*": [".mp3", ".wav", ".m4a", ".ogg"],
		},
		maxSize: 100 * 1024 * 1024, // 100MB
		multiple: false,
		disabled: inputMode === "record",
	});

	const handleRecordingComplete = (blob: Blob) => {
		setRecordedBlob(blob);
		setError(null);
	};

	const handleRecordingReset = () => {
		setRecordedBlob(null);
	};

	const handleSubmitRecording = async () => {
		if (!recordedBlob) return;

		setError(null);
		setIsUploading(true);

		try {
			// Convert blob to File
			const file = new File([recordedBlob], `recording-${Date.now()}.webm`, {
				type: "audio/webm",
			});

			const response = await api.generatePresentation(file, {
				theme,
				includeImages,
				interactiveMode,
				saveTranscription,
			});

			navigate(`/job/${response.job_id}`);
		} catch (err: any) {
			const detail = err.response?.data?.detail;
			// Handle both string and object error formats
			const errorMessage = typeof detail === 'string'
				? detail
				: detail?.message || detail?.error || "Failed to process recording";
			setError(errorMessage);
		} finally {
			setIsUploading(false);
		}
	};

	return (
		<div className="min-h-screen flex items-center justify-center p-4">
			<div className="max-w-2xl w-full bg-white rounded-lg shadow-xl p-8">
				<h1 className="text-3xl font-bold text-gray-900 mb-2">Voice-to-Slide Generator</h1>
				<p className="text-gray-600 mb-8">Convert your voice recordings into professional presentations</p>

				{/* Mode Toggle Switch */}
				<div className="mb-8 flex items-center justify-center space-x-4">
					<button
						onClick={() => {
							setInputMode("upload");
							setRecordedBlob(null);
							setError(null);
						}}
						className={`flex items-center space-x-2 px-6 py-3 rounded-lg transition-colors ${
							inputMode === "upload"
								? "bg-blue-600 text-white shadow-lg"
								: "bg-gray-200 text-gray-700 hover:bg-gray-300"
						}`}
					>
						<Upload className="h-5 w-5" />
						<span>Upload File</span>
					</button>

					<button
						onClick={() => {
							setInputMode("record");
							setError(null);
						}}
						className={`flex items-center space-x-2 px-6 py-3 rounded-lg transition-colors ${
							inputMode === "record"
								? "bg-red-600 text-white shadow-lg"
								: "bg-gray-200 text-gray-700 hover:bg-gray-300"
						}`}
					>
						<Mic className="h-5 w-5" />
						<span>Record Audio</span>
					</button>
				</div>

				{/* Upload Mode */}
				{inputMode === "upload" && (
					<div
						{...getRootProps()}
						className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
							isDragActive ? "border-blue-500 bg-blue-50" : "border-gray-300 hover:border-blue-400 hover:bg-gray-50"
						}`}
					>
						<input {...getInputProps()} />
						<Upload className="mx-auto h-12 w-12 text-gray-400 mb-4" />
						{isDragActive ? (
							<p className="text-lg text-blue-600">Drop the audio file here...</p>
						) : (
							<>
								<p className="text-lg text-gray-700 mb-2">Drop audio file here or click to browse</p>
								<p className="text-sm text-gray-500">Supported: MP3, WAV, M4A, OGG (max 100MB)</p>
							</>
						)}
					</div>
				)}

				{/* Record Mode */}
				{inputMode === "record" && (
					<div className="border-2 border-dashed border-red-300 rounded-lg p-8 bg-red-50">
						<AudioRecorder onRecordingComplete={handleRecordingComplete} onReset={handleRecordingReset} />

						{recordedBlob && (
							<button
								onClick={handleSubmitRecording}
								disabled={isUploading}
								className="mt-6 w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 font-medium"
							>
								{isUploading ? "Processing..." : "Generate Presentation"}
							</button>
						)}
					</div>
				)}

				{error && <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">{error}</div>}

				{/* Configuration */}
				<div className="mt-8 space-y-4">
					<h2 className="text-lg font-semibold text-gray-900">Configuration</h2>

					<div>
						<label className="block text-sm font-medium text-gray-700 mb-2">Theme</label>
						<select
							value={theme}
							onChange={(e) => setTheme(e.target.value)}
							className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-black"
						>
							<option>Modern Professional</option>
							<option>Dark Mode</option>
							<option>Vibrant Creative</option>
							<option>Minimal Clean</option>
							<option>Corporate Blue</option>
						</select>
					</div>

					<div className="space-y-2">
						<label className="flex items-center">
							<input type="checkbox" checked={includeImages} onChange={toggleImages} className="mr-2 h-4 w-4" />
							<span className="text-sm text-gray-700">Include images from Unsplash</span>
						</label>

						<label className="flex items-center">
							<input type="checkbox" checked={interactiveMode} onChange={toggleInteractive} className="mr-2 h-4 w-4" />
							<span className="text-sm text-gray-700">Interactive mode (edit structure before generating)</span>
						</label>

						<label className="flex items-center">
							<input type="checkbox" checked={saveTranscription} onChange={toggleSaveTranscription} className="mr-2 h-4 w-4" />
							<span className="text-sm text-gray-700">Save transcription</span>
						</label>
					</div>
				</div>

				{isUploading && inputMode === "upload" && <div className="mt-6 text-center text-blue-600">Uploading...</div>}
			</div>
		</div>
	);
}
