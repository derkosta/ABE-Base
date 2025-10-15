'use client';

import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { useMutation, useQueryClient } from 'react-query';
import Layout from '@/components/Layout';
import { apiClient } from '@/lib/api';
import { Upload, FileText, X, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';
import { useRouter } from 'next/navigation';

interface UploadedFile {
  file: File;
  id: string;
  status: 'pending' | 'uploading' | 'success' | 'error';
  progress: number;
  error?: string;
  result?: any;
}

export default function UploadPage() {
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([]);
  const [title, setTitle] = useState('');
  const queryClient = useQueryClient();
  const router = useRouter();

  const uploadMutation = useMutation(apiClient.uploadDocument, {
    onSuccess: (data, variables) => {
      setUploadedFiles(prev => 
        prev.map(f => 
          f.id === variables.id 
            ? { ...f, status: 'success', progress: 100, result: data }
            : f
        )
      );
      toast.success(`Dokument "${variables.file.name}" erfolgreich hochgeladen`);
      queryClient.invalidateQueries('search');
    },
    onError: (error: any, variables) => {
      setUploadedFiles(prev => 
        prev.map(f => 
          f.id === variables.id 
            ? { 
                ...f, 
                status: 'error', 
                error: error.response?.data?.detail || 'Upload fehlgeschlagen'
              }
            : f
        )
      );
      toast.error(`Upload fehlgeschlagen: ${variables.file.name}`);
    },
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: UploadedFile[] = acceptedFiles.map(file => ({
      file,
      id: Math.random().toString(36).substr(2, 9),
      status: 'pending',
      progress: 0,
    }));

    setUploadedFiles(prev => [...prev, ...newFiles]);

    // Start upload for each file
    newFiles.forEach(fileObj => {
      uploadMutation.mutate({
        file: fileObj.file,
        title: title || fileObj.file.name,
        id: fileObj.id,
      });

      // Update status to uploading
      setUploadedFiles(prev => 
        prev.map(f => 
          f.id === fileObj.id 
            ? { ...f, status: 'uploading' }
            : f
        )
      );
    });
  }, [title, uploadMutation]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf']
    },
    maxSize: 50 * 1024 * 1024, // 50MB
    multiple: true,
  });

  const removeFile = (id: string) => {
    setUploadedFiles(prev => prev.filter(f => f.id !== id));
  };

  const clearAll = () => {
    setUploadedFiles([]);
    setTitle('');
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <FileText className="w-5 h-5 text-gray-400" />;
      case 'uploading':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'success':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-red-500" />;
      default:
        return <FileText className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-800';
      case 'uploading':
        return 'bg-blue-100 text-blue-800';
      case 'success':
        return 'bg-green-100 text-green-800';
      case 'error':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <Layout requireAuth={true}>
      <div className="max-w-4xl mx-auto space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Dokumente hochladen
          </h1>
          <p className="text-gray-600">
            Laden Sie ABE/Homologation PDFs hoch
          </p>
        </div>

        <div className="card">
          <div className="card-body">
            <div className="space-y-4">
              {/* Title input */}
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Titel (optional)
                </label>
                <input
                  type="text"
                  id="title"
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  className="input"
                  placeholder="Titel für alle hochgeladenen Dokumente"
                />
              </div>

              {/* Dropzone */}
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? 'border-primary-400 bg-primary-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input {...getInputProps()} />
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                {isDragActive ? (
                  <p className="text-lg text-primary-600">
                    Dateien hier ablegen...
                  </p>
                ) : (
                  <div>
                    <p className="text-lg text-gray-600 mb-2">
                      PDF-Dateien hier ablegen oder klicken zum Auswählen
                    </p>
                    <p className="text-sm text-gray-500">
                      Nur PDF-Dateien bis 50MB
                    </p>
                  </div>
                )}
              </div>

              {/* File list */}
              {uploadedFiles.length > 0 && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-medium text-gray-900">
                      Hochgeladene Dateien ({uploadedFiles.length})
                    </h3>
                    <button
                      onClick={clearAll}
                      className="text-sm text-gray-500 hover:text-gray-700"
                    >
                      Alle löschen
                    </button>
                  </div>

                  <div className="space-y-2">
                    {uploadedFiles.map((fileObj) => (
                      <div
                        key={fileObj.id}
                        className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                      >
                        <div className="flex items-center space-x-3 flex-1 min-w-0">
                          {getStatusIcon(fileObj.status)}
                          <div className="flex-1 min-w-0">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {fileObj.file.name}
                            </p>
                            <p className="text-xs text-gray-500">
                              {(fileObj.file.size / (1024 * 1024)).toFixed(2)} MB
                            </p>
                            {fileObj.status === 'uploading' && (
                              <div className="mt-1">
                                <div className="bg-gray-200 rounded-full h-2">
                                  <div
                                    className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                                    style={{ width: `${fileObj.progress}%` }}
                                  />
                                </div>
                              </div>
                            )}
                            {fileObj.error && (
                              <p className="text-xs text-red-600 mt-1">
                                {fileObj.error}
                              </p>
                            )}
                          </div>
                        </div>

                        <div className="flex items-center space-x-2">
                          <span className={`badge ${getStatusColor(fileObj.status)}`}>
                            {fileObj.status === 'pending' && 'Wartend'}
                            {fileObj.status === 'uploading' && 'Upload...'}
                            {fileObj.status === 'success' && 'Erfolgreich'}
                            {fileObj.status === 'error' && 'Fehler'}
                          </span>

                          {fileObj.status === 'success' && (
                            <button
                              onClick={() => router.push(`/doc/${fileObj.result.document.id}`)}
                              className="text-sm text-primary-600 hover:text-primary-700"
                            >
                              Anzeigen
                            </button>
                          )}

                          <button
                            onClick={() => removeFile(fileObj.id)}
                            className="text-gray-400 hover:text-gray-600"
                          >
                            <X className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Info box */}
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <FileText className="h-5 w-5 text-blue-400" />
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-blue-800">
                Upload-Informationen
              </h3>
              <div className="mt-2 text-sm text-blue-700">
                <ul className="list-disc list-inside space-y-1">
                  <li>Nur PDF-Dateien werden akzeptiert</li>
                  <li>Maximale Dateigröße: 50MB</li>
                  <li>Dokumente werden automatisch mit OCR verarbeitet</li>
                  <li>E-Nummern werden automatisch extrahiert</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
