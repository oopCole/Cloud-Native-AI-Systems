"use client";

import { useState } from "react";
import { useCompletion } from "@ai-sdk/react";

export default function Home() {
  const {
    completion,
    complete,
    error,
    isLoading,
    input,
    handleInputChange,
  } = useCompletion();

  const [validationError, setValidationError] = useState("");

  function handleGenerate() {
    setValidationError("");
    const trimmed = input.trim();
    if (!trimmed) {
      setValidationError("Please enter some text.");
      return;
    }
    complete(trimmed);
  }

  return (
    <main
      style={{
        padding: "2rem",
        maxWidth: "800px",
        margin: "0 auto",
      }}
    >
      <h1>Summarize</h1>

      <label style={{ display: "block", marginBottom: "0.25rem" }}>
        Input text
      </label>
      <textarea
        value={input}
        onChange={handleInputChange}
        placeholder="Enter text to summarize..."
        rows={6}
        disabled={isLoading}
        style={{
          width: "100%",
          padding: "0.5rem",
          marginBottom: "1rem",
          boxSizing: "border-box",
        }}
      />

      <button
        type="button"
        onClick={handleGenerate}
        disabled={isLoading}
        style={{ padding: "0.5rem 1rem", marginBottom: "1rem" }}
      >
        Generate Summary
      </button>

      {isLoading ? (
        <div style={{ marginBottom: "1rem", color: "#666" }}>
          Loading…
        </div>
      ) : null}

      {(validationError || error) ? (
        <div
          role="alert"
          style={{
            color: "darkred",
            marginBottom: "1rem",
            padding: "0.5rem",
            background: "#fee",
          }}
        >
          {validationError || error?.message}
        </div>
      ) : null}

      <label style={{ display: "block", marginBottom: "0.25rem" }}>
        Output
      </label>
      <div
        style={{
          minHeight: "4rem",
          padding: "0.5rem",
          marginBottom: "1rem",
          background: "#f5f5f5",
          border: "1px solid #ccc",
        }}
      >
        {completion || "—"}
      </div>
    </main>
  );
}
