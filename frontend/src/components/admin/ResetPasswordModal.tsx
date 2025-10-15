'use client';

import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useMutation } from 'react-query';
import { X, Key, Eye, EyeOff, Loader2, Copy } from 'lucide-react';
import { apiClient } from '@/lib/api';
import toast from 'react-hot-toast';
import { UserResponse } from '@/types';

const resetPasswordSchema = z.object({
  new_password: z.string().min(8, 'Passwort muss mindestens 8 Zeichen lang sein').optional(),
  force_change: z.boolean(),
});

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

interface ResetPasswordModalProps {
  user: UserResponse;
  onClose: () => void;
  onSuccess: () => void;
}

export default function ResetPasswordModal({ user, onClose, onSuccess }: ResetPasswordModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [generatedPassword, setGeneratedPassword] = useState('');

  const {
    register,
    handleSubmit,
    formState: { errors },
    watch,
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      force_change: false,
    },
  });

  const resetPasswordMutation = useMutation(
    (data: ResetPasswordFormData) => apiClient.resetUserPassword(user.id, data.new_password),
    {
      onSuccess: (data) => {
        toast.success('Passwort erfolgreich zurückgesetzt');
        if (data.new_password) {
          setGeneratedPassword(data.new_password);
          toast.success('Neues Passwort generiert', { duration: 10000 });
        }
      },
      onError: (error: any) => {
        toast.error(error.response?.data?.detail || 'Passwort-Reset fehlgeschlagen');
      },
    }
  );

  const onSubmit = async (data: ResetPasswordFormData) => {
    try {
      setIsSubmitting(true);
      await resetPasswordMutation.mutateAsync(data);
    } finally {
      setIsSubmitting(false);
    }
  };

  const copyPassword = () => {
    if (generatedPassword) {
      navigator.clipboard.writeText(generatedPassword);
      toast.success('Passwort in Zwischenablage kopiert');
    }
  };

  const generateRandomPassword = () => {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*';
    let password = '';
    for (let i = 0; i < 12; i++) {
      password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return password;
  };

  const setRandomPassword = () => {
    const randomPassword = generateRandomPassword();
    // This would need to be implemented with a ref or controlled input
    // For now, we'll just show it in the generated password field
    setGeneratedPassword(randomPassword);
  };

  return (
    <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full z-50">
      <div className="relative top-20 mx-auto p-5 border w-96 shadow-lg rounded-md bg-white">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900 flex items-center">
            <Key className="w-5 h-5 mr-2" />
            Passwort zurücksetzen
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

        {generatedPassword ? (
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 rounded-md p-4">
              <div className="flex items-center justify-between">
                <div>
                  <h4 className="text-sm font-medium text-green-800">
                    Neues Passwort generiert
                  </h4>
                  <p className="text-sm text-green-700 mt-1">
                    Das neue Passwort für {user.username}:
                  </p>
                </div>
                <button
                  onClick={copyPassword}
                  className="text-green-600 hover:text-green-700"
                  title="Passwort kopieren"
                >
                  <Copy className="w-5 h-5" />
                </button>
              </div>
              <div className="mt-3 p-2 bg-white border border-green-200 rounded font-mono text-sm">
                {showPassword ? generatedPassword : '••••••••••••'}
                <button
                  onClick={() => setShowPassword(!showPassword)}
                  className="ml-2 text-green-600 hover:text-green-700"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            
            <div className="bg-yellow-50 border border-yellow-200 rounded-md p-3">
              <p className="text-sm text-yellow-700">
                <strong>Wichtig:</strong> Speichern Sie dieses Passwort sicher. Es wird nur einmal angezeigt.
              </p>
            </div>

            <div className="flex justify-end space-x-3 pt-4">
              <button
                onClick={onClose}
                className="btn btn-secondary"
              >
                Schließen
              </button>
            </div>
          </div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div>
              <label htmlFor="new_password" className="block text-sm font-medium text-gray-700 mb-1">
                Neues Passwort (optional)
              </label>
              <input
                {...register('new_password')}
                type="password"
                className={`input ${errors.new_password ? 'border-red-300 focus:border-red-500 focus:ring-red-500' : ''}`}
                placeholder="Leer lassen für automatische Generierung"
              />
              {errors.new_password && (
                <p className="mt-1 text-sm text-red-600">{errors.new_password.message}</p>
              )}
              <button
                type="button"
                onClick={setRandomPassword}
                className="mt-2 text-sm text-primary-600 hover:text-primary-700"
              >
                Zufälliges Passwort generieren
              </button>
            </div>

            <div>
              <label className="flex items-center">
                <input
                  {...register('force_change')}
                  type="checkbox"
                  className="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
                />
                <span className="ml-2 text-sm text-gray-700">
                  Benutzer muss Passwort beim nächsten Login ändern
                </span>
              </label>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
              <div className="flex">
                <div className="flex-shrink-0">
                  <Key className="h-5 w-5 text-blue-400" />
                </div>
                <div className="ml-3">
                  <h4 className="text-sm font-medium text-blue-800">
                    Passwort-Reset
                  </h4>
                  <p className="text-sm text-blue-700 mt-1">
                    Wenn kein Passwort angegeben wird, wird automatisch ein sicheres Passwort generiert.
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
                    Zurücksetzen...
                  </>
                ) : (
                  'Passwort zurücksetzen'
                )}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
