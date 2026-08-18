import React, { useState } from 'react';

/**
 * Reusable Drag-and-Drop CSV/XLSX File Upload Zone
 * Allows clinicians to upload EHR export files to auto-fill patient assessment parameters.
 */
export default function FileUploadZone({
  onFileSelect,
  isUploading = false,
  acceptedFormats = '.csv,.xlsx,.xls',
  label = 'Drag & drop patient dataset file (CSV/Excel) or click to browse'
}) {
  const [dragActive, setDragActive] = useState(false);
  const [selectedFileName, setSelectedFileName] = useState('');

  function handleDrag(e) {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  }

  function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      setSelectedFileName(file.name);
      onFileSelect(file);
    }
  }

  function handleChange(e) {
    e.preventDefault();
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      setSelectedFileName(file.name);
      onFileSelect(file);
    }
  }

  return (
    <div
      className="file-upload-zone"
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      style={{
        border: `2px dashed ${dragActive ? 'var(--accent)' : 'var(--border)'}`,
        background: dragActive ? 'var(--surface-muted)' : 'var(--surface)',
        borderRadius: '12px',
        padding: '20px',
        textAlign: 'center',
        cursor: 'pointer',
        transition: 'all 0.2s ease',
        marginBottom: '16px'
      }}
    >
      <input
        type="file"
        id="file-upload-input"
        accept={acceptedFormats}
        onChange={handleChange}
        style={{ display: 'none' }}
        disabled={isUploading}
      />
      <label htmlFor="file-upload-input" style={{ cursor: 'pointer', display: 'block' }}>
        <svg
          width="32"
          height="32"
          viewBox="0 0 24 24"
          fill="none"
          stroke="var(--accent)"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          style={{ margin: '0 auto 8px auto' }}
        >
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>
        <span style={{ fontSize: '0.9rem', color: 'var(--text)', fontWeight: 500, display: 'block' }}>
          {selectedFileName ? `Selected: ${selectedFileName}` : label}
        </span>
        <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)', display: 'block', marginTop: '4px' }}>
          {isUploading ? 'Parsing file & extracting parameters…' : 'Supported: .csv, .xlsx, .xls'}
        </span>
      </label>
    </div>
  );
}
