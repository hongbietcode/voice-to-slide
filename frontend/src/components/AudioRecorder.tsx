import { useState, useRef, useEffect } from "react";
import { Mic, Square, Pause, Play, Trash2 } from "lucide-react";

interface AudioRecorderProps {
	onRecordingComplete: (audioBlob: Blob) => void;
	onReset?: () => void;
}

export default function AudioRecorder({ onRecordingComplete, onReset }: AudioRecorderProps) {
	const [isRecording, setIsRecording] = useState(false);
	const [isPaused, setIsPaused] = useState(false);
	const [recordingTime, setRecordingTime] = useState(0);
	const [audioBlob, setAudioBlob] = useState<Blob | null>(null);
	const [audioUrl, setAudioUrl] = useState<string | null>(null);

	const mediaRecorderRef = useRef<MediaRecorder | null>(null);
	const chunksRef = useRef<Blob[]>([]);
	const timerRef = useRef<number | null>(null);

	useEffect(() => {
		return () => {
			if (timerRef.current) {
				clearInterval(timerRef.current);
			}
			if (audioUrl) {
				URL.revokeObjectURL(audioUrl);
			}
		};
	}, [audioUrl]);

	const startRecording = async () => {
		try {
			const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
			const mediaRecorder = new MediaRecorder(stream);
			mediaRecorderRef.current = mediaRecorder;
			chunksRef.current = [];

			mediaRecorder.ondataavailable = (event) => {
				if (event.data.size > 0) {
					chunksRef.current.push(event.data);
				}
			};

			mediaRecorder.onstop = () => {
				const blob = new Blob(chunksRef.current, { type: "audio/webm" });
				setAudioBlob(blob);
				const url = URL.createObjectURL(blob);
				setAudioUrl(url);
				onRecordingComplete(blob);

				// Stop all tracks
				stream.getTracks().forEach((track) => track.stop());
			};

			mediaRecorder.start();
			setIsRecording(true);
			setIsPaused(false);

			// Start timer
			timerRef.current = setInterval(() => {
				setRecordingTime((prev) => prev + 1);
			}, 1000);
		} catch (error) {
			console.error("Error accessing microphone:", error);
			alert("Could not access microphone. Please grant permission and try again.");
		}
	};

	const pauseRecording = () => {
		if (mediaRecorderRef.current && mediaRecorderRef.current.state === "recording") {
			mediaRecorderRef.current.pause();
			setIsPaused(true);
			if (timerRef.current) {
				clearInterval(timerRef.current);
			}
		}
	};

	const resumeRecording = () => {
		if (mediaRecorderRef.current && mediaRecorderRef.current.state === "paused") {
			mediaRecorderRef.current.resume();
			setIsPaused(false);
			timerRef.current = setInterval(() => {
				setRecordingTime((prev) => prev + 1);
			}, 1000);
		}
	};

	const stopRecording = () => {
		if (mediaRecorderRef.current) {
			mediaRecorderRef.current.stop();
			setIsRecording(false);
			setIsPaused(false);
			if (timerRef.current) {
				clearInterval(timerRef.current);
			}
		}
	};

	const resetRecording = () => {
		setRecordingTime(0);
		setAudioBlob(null);
		if (audioUrl) {
			URL.revokeObjectURL(audioUrl);
			setAudioUrl(null);
		}
		if (onReset) {
			onReset();
		}
	};

	const formatTime = (seconds: number) => {
		const mins = Math.floor(seconds / 60);
		const secs = seconds % 60;
		return `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;
	};

	return (
		<div className="space-y-4">
			{/* Recording Controls */}
			{!audioBlob && (
				<div className="flex flex-col items-center space-y-4">
					<div className="text-4xl font-mono text-gray-700">{formatTime(recordingTime)}</div>

					<div className="flex space-x-4">
						{!isRecording ? (
							<button
								onClick={startRecording}
								className="flex items-center space-x-2 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
							>
								<Mic className="h-5 w-5" />
								<span>Start Recording</span>
							</button>
						) : (
							<>
								{!isPaused ? (
									<button
										onClick={pauseRecording}
										className="flex items-center space-x-2 px-6 py-3 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
									>
										<Pause className="h-5 w-5" />
										<span>Pause</span>
									</button>
								) : (
									<button
										onClick={resumeRecording}
										className="flex items-center space-x-2 px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
									>
										<Play className="h-5 w-5" />
										<span>Resume</span>
									</button>
								)}

								<button
									onClick={stopRecording}
									className="flex items-center space-x-2 px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 transition-colors"
								>
									<Square className="h-5 w-5" />
									<span>Stop</span>
								</button>
							</>
						)}
					</div>

					{isRecording && (
						<div className="flex items-center space-x-2 text-red-600">
							<div className="w-3 h-3 bg-red-600 rounded-full animate-pulse"></div>
							<span className="text-sm font-medium">{isPaused ? "Paused" : "Recording..."}</span>
						</div>
					)}
				</div>
			)}

			{/* Playback Controls */}
			{audioBlob && audioUrl && (
				<div className="space-y-4">
					<div className="text-center text-gray-700">
						<p className="font-medium">Recording Complete!</p>
						<p className="text-sm text-gray-500">Duration: {formatTime(recordingTime)}</p>
					</div>

					<audio controls src={audioUrl} className="w-full" />

					<button
						onClick={resetRecording}
						className="flex items-center justify-center space-x-2 w-full px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
					>
						<Trash2 className="h-4 w-4" />
						<span>Delete & Record Again</span>
					</button>
				</div>
			)}
		</div>
	);
}
