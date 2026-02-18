"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useAuth } from "@/context/auth";

export default function PDFViewerPage() {
  const params = useParams();
  const docId = params.id as string;
  const { user } = useAuth();

  // Use API proxy so the request includes the auth cookie
  const proxyUrl = `/apiProxy/files/${docId}/stream`;

  return (
    <div className="flex h-[calc(100vh-4rem)] flex-col p-4">
      <Link
        href={user?.role === "inmate" ? "/inmate" : "/cases"}
        className="mb-2 inline-block text-blue-600 hover:underline"
      >
        ← Back
      </Link>
      <div className="flex-1 overflow-hidden rounded border border-gray-200">
        <object
          data={proxyUrl}
          type="application/pdf"
          className="h-full w-full"
          aria-label="PDF document"
        >
          <p className="p-4 text-gray-600">
            PDF cannot be displayed.{" "}
            <a href={proxyUrl} download className="text-blue-600 hover:underline">
              Download instead
            </a>
          </p>
        </object>
      </div>
    </div>
  );
}
