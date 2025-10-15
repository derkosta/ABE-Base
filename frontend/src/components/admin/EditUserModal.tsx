'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from 'react-query';
import { X, User, Mail, Shield, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';
import { UserResponse } from '@/types';

const editUserSchema = z.object({
  email: z.string().email('Ungültige E-Mail-Adresse').optional().or(z.literal('')),
  role: z.enum(['admin', 'user'], {
    required_error: 'Rolle ist erforderlich',
  }),
  is_active: z.boolean(),
});

type EditUserFormData = z.infer<typeof editUserSchema>;

interface EditUserModalProps {
  user: UserResponse;
  onClose: () => void;
  onSuccess: () => void;
}

export default function EditUserModal({ user, onClose, onSuccess }: EditUserModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<EditUserFormData>({
    resolver: zodResolver(editUserSchema),
    defaultValues: {
      email: user.email || '',
      role: user.role as 'admin' | 'user',
      is_active: user.is_active,
    },
  });

  const updateUserMutation = useMutation(
    (data: EditUserFormData) => apiClient.updateUser(user.id, data),
    {
      onSuccess: () => {
        toast.success('Benutzer erfolgreich aktualisiert');
        onSuccess();
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Aktualisierung fehlgeschlagen');
      },
    }
  );

  const onSubmit = async (data: EditUserFormData) => {
    try {
      setIsSubmitting(true);
      await updateUserMutation.mutateAsync({
        email: data.email || undefined,
        role: data.role,
        is_active: data.is_active,
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <User className="w-5 h-5 mr-2" />
            Benutzer bearbeiten
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="mb-4 p-3 bg-gray-50 rounded-md">
          <p className="text-sm text-gray-600">
            <span className="font-medium">Benutzer:</span> {user.username}
          </p>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
              E-Mail (optional)
            </label>
            <input
              {...register('email')}
              type="email"
              className={`input ${errors.email ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
              placeholder="E-Mail-Adresse eingeben"
            />
            {errors.email && (
              <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
            )}
          </div>

          <div>
            <label htmlFor="role" className="block text-sm font-medium text-gray-700 mb-1">
              Rolle *
            </label>
            <select
              {...register('role')}
              className={`input ${errors.role ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
            >
              <option value="user">Benutzer</option>
              <option value="admin">Administrator</option>
            </select>
            {errors.role && (
              <p className="mt-1 text-sm text-red-600">{errors.role.message}</p>
            )}
          </div>

          <div>
            <label className="flex items-center">
              <input
                {...register('is_active')}
                type="checkbox"
                className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">
                Benutzer ist aktiv
              </span>
            </label>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
            <div className="flex">
              <div className="flex-shrink-0">
                <Shield className="h-5 w-5 text-yellow-400" />
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-yellow-800">
                  Hinweis
                </h4>
                <p className="text-sm text-yellow-700 mt-1">
                  Benutzername kann nicht geändert werden. Für Passwort-Änderungen verwenden Sie "Passwort zurücksetzen".
                </p>
              </div>
            </div>
          </div>

          <div className="flex justify-end space-x-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="btn btn-secondary"
            >
              Abbrechen
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="btn btn-primary"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Speichern...
                </>
              ) : (
                'Änderungen speichern'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
