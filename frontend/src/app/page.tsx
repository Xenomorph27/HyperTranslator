import WebcamCapture from "@/components/WebcamCapture";
import VideoUpload from "@/components/VideoUpload";
import TranslationDisplay from "@/components/TranslationDisplay";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <div className="z-10 w-full max-w-5xl items-center justify-between font-mono text-sm lg:flex flex-col">
        <h1 className="text-4xl font-bold mb-8">ISL Translator</h1>
        <p className="mb-12 text-center text-gray-500">
          Indian Sign Language to English Translator. Ensure you are well lit and in frame.
        </p>

        <div className="w-full flex flex-col md:flex-row gap-8 justify-center">
          <div className="w-full md:w-1/2 p-4 border rounded-xl border-gray-200">
            <WebcamCapture />
          </div>
          <div className="w-full md:w-1/2 p-4 border rounded-xl border-gray-200">
            <VideoUpload />
          </div>
        </div>

        <div className="mt-12 w-full p-6 border rounded-xl border-gray-200 bg-gray-50">
          <TranslationDisplay />
        </div>
      </div>
    </main>
  );
}
