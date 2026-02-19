"use client";

import { useState } from "react";

const FAQ = [
  {
    q: "How do I view my documents?",
    a: "Tap Documents in the bottom bar. Your attorney shares documents here. Tap any document to open and read it.",
  },
  {
    q: "What is Similar Cases?",
    a: "Similar Cases helps you find court opinions that may relate to your situation. Type a legal topic (e.g. habeas corpus, sentencing) and browse results. Use filters to narrow by jurisdiction or outcome.",
  },
  {
    q: "Can I save documents offline?",
    a: "Use the Save offline button when viewing a document. Saved documents will be available without internet. Not all documents support offline saving.",
  },
  {
    q: "How do I contact my attorney?",
    a: "Contact your attorney through your facility’s approved channels. This app does not include messaging.",
  },
  {
    q: "What if a document won’t load?",
    a: "Check your connection (see status at the bottom of My Case). If you’re offline, try again when back online. You can also try the Download button to save the file.",
  },
] as const;

export default function InmateHelpPage() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <div className="mx-auto max-w-2xl px-4 py-6 text-base">
      <h2 className="mb-6 text-xl font-semibold text-stone-800">
        Frequently asked questions
      </h2>
      <div className="space-y-3">
        {FAQ.map((item, i) => (
          <div
            key={i}
            className="rounded-2xl border border-stone-200 bg-white shadow-sm overflow-hidden"
          >
            <button
              onClick={() => setOpenIndex(openIndex === i ? null : i)}
              className="flex min-h-[56px] w-full items-center justify-between px-5 py-4 text-left font-medium text-stone-800 hover:bg-stone-50"
            >
              {item.q}
              <span className="text-xl text-stone-400">
                {openIndex === i ? "−" : "+"}
              </span>
            </button>
            {openIndex === i && (
              <div className="border-t border-stone-100 px-5 py-4 text-stone-600">
                {item.a}
              </div>
            )}
          </div>
        ))}
      </div>

      <div className="mt-8 rounded-2xl border border-amber-200 bg-amber-50/50 p-5">
        <h3 className="font-semibold text-stone-800">Need more help?</h3>
        <p className="mt-2 text-stone-600">
          Reach out to your attorney or facility staff for assistance with your
          case.
        </p>
      </div>
    </div>
  );
}
