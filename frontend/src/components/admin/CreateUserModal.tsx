'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from 'react-query';
import { X, User, Mail, Shield, Loader2 } from 'lucide-react';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';

const createUserSchema = z.object({
  username: z.string().min(3, 'Benutzername muss mindestens 3 Zeichen lang sein'),
  email: z.string().email('Ungültige E-Mail-Adresse').optional().or(z.literal('')),
  role: z.enum(['admin', 'user'], {
    required_error: 'Rolle ist erforderlich',
  }),
});

type CreateUserFormData = z.infer<typeof createUserSchema>;

interface CreateUserModalProps {
  onClose: () => void;
  onSuccess: () => void;
}

export default function CreateUserModal({ onClose, onSuccess }: CreateUserModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
    reset,
  } = useForm<CreateUserFormData>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      role: 'user',
    },
  });

  const createUserMutation = useMutation(apiClient.createUser, {
    onSuccess: (data) => {
      toast.success('Benutzer erfolgreich erstellt');
      if (data[1]?.temp_password) {
        toast.success(`Temporäres Passwort: ${data[1].temp_password}`, {
          duration: 10000,
        });
      }
      onSuccess();
      reset();
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Erstellung fehlgeschlagen');
    },
  });

  const onSubmit = async (data: CreateUserFormData) => {
    try {
      setIsSubmitting(true);
      await createUserMutation.mutateAsync({
        username: data.username,
        email: data.email || undefined,
        role: data.role,
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
            Neuer Benutzer
          </h3>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
              Benutzername *
            </label>
            <input
              {...register('username')}
              type="text"
              className={`input ${errors.username ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
              placeholder="Benutzername eingeben"
            />
            {errors.username && (
              <p className="mt-1 text-sm text-red-600">{errors.username.message}</p>
            )}
          </div>

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

          <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
            <div className="flex">
              <div className="flex-shrink-0">
                <Shield className="h-5 w-5 text-blue-400" />
              </div>
              <div className="ml-3">
                <h4 className="text-sm font-medium text-blue-800">
                  Automatisches Passwort
                </h4>
                <p className="text-sm text-blue-700 mt-1">
                  Ein sicheres temporäres Passwort wird automatisch generiert und nach der Erstellung angezeigt.
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
                  Erstellen...
                </>
              ) : (
                'Benutzer erstellen'
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
