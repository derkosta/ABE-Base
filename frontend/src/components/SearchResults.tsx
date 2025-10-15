'use client';

import { useState } from 'react';
import Link from 'next/link';
import { 
  FileText, 
  Download, 
  Calendar, 
  Tag,
  Search,
  AlertCircle,
  Loader2
} from 'lucide-react';
import { SearchResult } from '@/types';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

interface SearchResultsProps {
  results: SearchResult[];
  isLoading: boolean;
  error: any;
  query: string;
  enumbersFound: string[];
}

export default function SearchResults({ 
  results, 
  isLoading, 
  error, 
  query, 
  enumbersFound 
}: SearchResultsProps) {
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());

  const handleDownload = async (docId: string, title: string) => {
    try {
      setDownloadingIds(prev => new Set(prev).add(docId));
      await apiClient.downloadDocument(docId);
      toast.success(`Download gestartet: ${title}`);
    } catch (error) {
      toast.error('Download fehlgeschlagen');
    } finally {
      setDownloadingIds(prev => {
        const newSet = new Set(prev);
        newSet.delete(docId);
        return newSet;
      });
    }
  };

  const formatDate = (dateString: string) => {
    try {
      return new Date(dateString).toLocaleDateString('de-DE', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin text-primary-600 mx-auto mb-4" />
          <p className="text-gray-600">Suche wird durchgeführt...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <AlertCircle className="h-8 w-8 text-red-500 mx-auto mb-4" />
          <p className="text-gray-600">Fehler bei der Suche</p>
          <p className="text-sm text-gray-500 mt-1">
            {error?.response?.data?.detail || 'Unbekannter Fehler'}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Search summary */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900 flex items-center">
              <Search className="w-5 h-5 mr-2" />
              Suchergebnisse
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              {results.length} Ergebnis{results.length !== 1 ? 'se' : ''} für "{query}"
            </p>
          </div>
          {enumbersFound.length > 0 && (
            <div className="text-right">
              <p className="text-sm font-medium text-gray-900">E-Nummern gefunden:</p>
              <div className="flex flex-wrap gap-1 mt-1">
                {enumbersFound.map((enumber, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-100 text-primary-800"
                  >
                    {enumber}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Results */}
      {results.length === 0 ? (
        <div className="text-center py-12">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">
            Keine Ergebnisse gefunden
          </h3>
          <p className="text-gray-600">
            Versuchen Sie andere Suchbegriffe oder prüfen Sie die Schreibweise.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {results.map((result) => (
            <div
              key={result.doc_id}
              className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-2 mb-2">
                    <Link
                      href={`/doc/${result.doc_id}`}
                      className="text-lg font-semibold text-gray-900 hover:text-primary-600 truncate"
                    >
                      {result.title}
                    </Link>
                    {result.score && (
                      <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-green-100 text-green-800">
                        {Math.round(result.score * 100)}% Match
                      </span>
                    )}
                  </div>
                  
                  {result.snippet && (
                    <p className="text-gray-600 text-sm mb-3 line-clamp-2">
                      {result.snippet}
                    </p>
                  )}
                  
                  <div className="flex items-center space-x-4 text-sm text-gray-500">
                    <div className="flex items-center">
                      <Calendar className="w-4 h-4 mr-1" />
                      {formatDate(result.created)}
                    </div>
                    
                    {result.enumbers.length > 0 && (
                      <div className="flex items-center">
                        <Tag className="w-4 h-4 mr-1" />
                        <div className="flex flex-wrap gap-1">
                          {result.enumbers.slice(0, 3).map((enumber, index) => (
                            <span
                              key={index}
                              className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-800"
                            >
                              {enumber}
                            </span>
                          ))}
                          {result.enumbers.length > 3 && (
                            <span className="text-xs text-gray-500">
                              +{result.enumbers.length - 3} weitere
                            </span>
                          )}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
                
                <div className="flex items-center space-x-2 ml-4">
                  <Link
                    href={`/doc/${result.doc_id}`}
                    className="btn btn-secondary"
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    Anzeigen
                  </Link>
                  <button
                    onClick={() => handleDownload(result.doc_id, result.title)}
                    disabled={downloadingIds.has(result.doc_id)}
                    className="btn btn-primary"
                  >
                    {downloadingIds.has(result.doc_id) ? (
                      <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    ) : (
                      <Download className="w-4 h-4 mr-2" />
                    )}
                    Download
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
