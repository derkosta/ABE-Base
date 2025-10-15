import axios, { AxiosInstance, AxiosResponse } from 'axios';
import Cookies from 'js-cookie';
import toast from 'react-hot-toast';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_BACKEND_BASE_URL || '/api',
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = Cookies.get('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid
          Cookies.remove('access_token');
          window.location.href = '/login';
        } else if (error.response?.status === 403) {
          toast.error('Zugriff verweigert');
        } else if (error.response?.status >= 500) {
          toast.error('Server-Fehler. Bitte versuchen Sie es später erneut.');
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth endpoints
  async login(credentials: { username: string; password: string }): Promise<any> {
    const response = await this.client.post('/auth/login', credentials);
    return response.data;
  }

  async logout(): Promise<void> {
    await this.client.post('/auth/logout');
  }

  async getCurrentUser(): Promise<any> {
    const response = await this.client.get('/auth/me');
    return response.data;
  }

  async setupStatus(): Promise<any> {
    const response = await this.client.get('/auth/setup-status');
    return response.data;
  }

  async initialSetup(credentials: { username: string; password: string }): Promise<any> {
    const response = await this.client.post('/auth/setup', credentials);
    return response.data;
  }

  // Document endpoints
  async uploadDocument(file: File, title?: string): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    if (title) {
      formData.append('title', title);
    }

    const response = await this.client.post('/docs/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  async getDocument(docId: string): Promise<any> {
    const response = await this.client.get(`/docs/${docId}`);
    return response.data;
  }

  async downloadDocument(docId: string): Promise<void> {
    const response = await this.client.get(`/docs/${docId}/download`, {
      responseType: 'blob',
    });

    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${docId}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  }

  async getDocumentThumbnail(docId: string): Promise<string> {
    const response = await this.client.get(`/docs/${docId}/thumb`, {
      responseType: 'blob',
    });
    return URL.createObjectURL(response.data);
  }

  async getDocumentAudit(docId: string, limit = 20): Promise<any[]> {
    const response = await this.client.get(`/docs/${docId}/audit`, {
      params: { limit },
    });
    return response.data;
  }

  // Search endpoints
  async searchDocuments(query: string, limit = 50): Promise<any> {
    const response = await this.client.get('/search', {
      params: { q: query, limit },
    });
    return response.data;
  }

  async getSearchSuggestions(query: string, limit = 10): Promise<any> {
    const response = await this.client.get('/search/suggest', {
      params: { q: query, limit },
    });
    return response.data;
  }

  // User management endpoints (admin only)
  async getUsers(): Promise<any[]> {
    const response = await this.client.get('/users');
    return response.data;
  }

  async createUser(userData: any): Promise<any> {
    const response = await this.client.post('/users', userData);
    return response.data;
  }

  async updateUser(userId: string, userData: any): Promise<any> {
    const response = await this.client.put(`/users/${userId}`, userData);
    return response.data;
  }

  async deleteUser(userId: string): Promise<void> {
    await this.client.delete(`/users/${userId}`);
  }

  async resetUserPassword(userId: string, newPassword?: string): Promise<any> {
    const response = await this.client.post(`/users/${userId}/reset-password`, {
      new_password: newPassword,
    });
    return response.data;
  }

  // Admin endpoints
  async getAdminStats(): Promise<any> {
    const response = await this.client.get('/admin/stats');
    return response.data;
  }

  async getAuditLog(limit = 100, action?: string, userId?: string): Promise<any[]> {
    const response = await this.client.get('/admin/audit', {
      params: { limit, action, user_id: userId },
    });
    return response.data;
  }

  async getUserActivity(days = 30): Promise<any> {
    const response = await this.client.get('/admin/users/activity', {
      params: { days },
    });
    return response.data;
  }

  async checkPaperlessStatus(): Promise<any> {
    const response = await this.client.get('/admin/paperless/status');
    return response.data;
  }

  // Hook endpoints
  async hookSearch(request: any): Promise<any> {
    const response = await this.client.post('/hooks/search', request);
    return response.data;
  }

  async getDocumentMeta(docId: string, limit = 10): Promise<any> {
    const response = await this.client.get(`/hooks/doc/${docId}/meta`, {
      params: { limit },
    });
    return response.data;
  }
}

export const apiClient = new ApiClient();
