import { useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useJobStore } from "../stores/jobStore";
import { api } from "../api/client";

export default function EditorPage() {
	const { jobId } = useParams<{ jobId: string }>();
	const navigate = useNavigate();
	const { currentJob, updateStructure } = useJobStore();
	const [feedback, setFeedback] = useState("");
	const [isSubmitting, setIsSubmitting] = useState(false);

	const handleSubmitFeedback = async () => {
		if (!jobId || !feedback.trim()) return;

		setIsSubmitting(true);
		try {
			const response = await api.editStructure(jobId, feedback);
			updateStructure(response.updated_structure);
			setFeedback("");
		} catch (error) {
			console.error("Failed to edit structure:", error);
		} finally {
			setIsSubmitting(false);
		}
	};

	const handleConfirm = async () => {
		if (!jobId) return;

		try {
			await api.confirmGeneration(jobId);
			navigate(`/job/${jobId}`);
		} catch (error) {
			console.error("Failed to confirm generation:", error);
		}
	};

	if (!currentJob?.structure) {
		return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
	}

	return (
		<div className="min-h-screen p-8">
			<div className="max-w-6xl mx-auto">
				<div className="bg-white rounded-lg shadow-xl p-8 mb-6">
					<h1 className="text-2xl font-bold text-gray-900 mb-6">Edit Presentation Structure</h1>

					<div className="grid grid-cols-2 gap-8 text-black">
						{/* Structure Preview */}
						<div>
							<h2 className="text-lg font-semibold mb-4">Preview</h2>
							<div className="space-y-4">
								<div className="p-4 border rounded">
									<h3 className="font-bold">{currentJob.structure.title}</h3>
								</div>
								{currentJob.structure.slides.map((slide, idx) => (
									<div key={idx} className="p-4 border rounded">
										<h4 className="font-semibold mb-2">
											Slide {idx + 1}: {slide.title}
										</h4>
										<ul className="list-disc list-inside text-sm text-gray-600">
											{slide.bullet_points.map((point, i) => (
												<li key={i}>{point}</li>
											))}
										</ul>
										{slide.image_theme && <p className="text-xs text-gray-500 mt-2">Image: {slide.image_theme}</p>}
									</div>
								))}
							</div>
						</div>

						{/* Feedback Panel */}
						<div>
							<h2 className="text-lg font-semibold mb-4">Provide Feedback</h2>
							<textarea
								value={feedback}
								onChange={(e) => setFeedback(e.target.value)}
								placeholder="E.g., 'Change slide 2 title to Introduction' or 'Add a slide about AI ethics'"
								className="w-full h-40 p-4 border rounded resize-none"
							/>
							<div className="mt-4 space-y-2">
								<button
									onClick={handleSubmitFeedback}
									disabled={isSubmitting || !feedback.trim()}
									className="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
								>
									{isSubmitting ? "Submitting..." : "Submit Feedback"}
								</button>
								<button onClick={handleConfirm} className="w-full py-2 bg-green-600 text-white rounded hover:bg-green-700">
									Confirm & Generate PPTX
								</button>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>
	);
}
