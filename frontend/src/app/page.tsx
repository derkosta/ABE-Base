'use client';

import { useState } from 'react';
import { useQuery } from 'react-query';
import Layout from '@/components/Layout';
import SearchBar from '@/components/SearchBar';
import SearchResults from '@/components/SearchResults';
import { apiClient } from '@/lib/api';

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [hasSearched, setHasSearched] = useState(false);

  const { data: searchResults, isLoading, error } = useQuery(
    ['search', searchQuery],
    () => apiClient.searchDocuments(searchQuery),
    {
      enabled: searchQuery.length > 0 && hasSearched,
      staleTime: 1000 * 60 * 5, // 5 minutes
    }
  );

  const handleSearch = (query: string) => {
    setSearchQuery(query);
    setHasSearched(true);
  };

  return (
    <Layout requireAuth={true}>
      <div className="space-y-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            ABE/Homologation Dokumenten-Suche
          </h1>
          <p className="text-gray-600">
            Durchsuchen Sie Dokumente nach Modellnamen oder E-Nummern
          </p>
        </div>

        <div className="max-w-2xl mx-auto">
          <SearchBar onSearch={handleSearch} />
        </div>

        {hasSearched && (
          <SearchResults 
            results={searchResults?.results || []}
            isLoading={isLoading}
            error={error}
            query={searchQuery}
            enumbersFound={searchResults?.enumbers_found || []}
          />
        )}

        {!hasSearched && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-4">
                Suchtipps
              </h2>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">E-Nummer Suche</h3>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• e13*1234*5678*00</li>
                    <li>• e13 1234 5678 00</li>
                    <li>• e13-1234-5678-00</li>
                    <li>• e131234567800</li>
                  </ul>
                </div>
                <div>
                  <h3 className="font-medium text-gray-900 mb-2">Modell Suche</h3>
                  <ul className="text-sm text-gray-600 space-y-1">
                    <li>• BMW X5</li>
                    <li>• Mercedes-Benz C-Klasse</li>
                    <li>• Audi A4</li>
                    <li>• Volkswagen Golf</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </Layout>
  );
}
