import React from 'react';
import type { AppProps } from 'next/app';
import Head from 'next/head';
import { GoogleOAuthProvider } from '@react-oauth/google';
import ErrorBoundary from '@/components/ErrorBoundary';
import { DebugProvider } from '@/contexts/DebugContext';
import { AuthProvider } from '@/contexts/AuthContext';
import logger from '@/utils/logger';
import { env, isDevelopment } from '@/config/environment';
import '@/styles/globals.css';

// Report unhandled promise rejections
if (typeof window !== 'undefined') {
  window.addEventListener('unhandledrejection', (event) => {
    logger.error('Unhandled Promise Rejection:', event.reason);
    
    // Track with analytics or error reporting service
    // if (!isDevelopment) {
    //   // Example: send to error tracking service
    //   // errorTrackingService.captureException(event.reason);
    // }
  });
  
  // Report uncaught errors
  window.addEventListener('error', (event) => {
    logger.error('Uncaught Error:', event.error || event.message);
    
    // Track with analytics or error reporting service
    // if (!isDevelopment) {
    //   // Example: send to error tracking service
    //   // errorTrackingService.captureException(event.error);
    // }
  });
}

// Custom error handler for error boundary
const handleError = (error: Error) => {
  logger.error('Error caught by root ErrorBoundary:', error);
  
  // Track with analytics or error reporting service
  // if (!isDevelopment) {
  //   // Example: send to error tracking service
  //   // errorTrackingService.captureException(error);
  // }
};

function MyApp({ Component, pageProps }: AppProps) {
  // Log when app renders (helpful for debugging during refreshes/navigation)
  React.useEffect(() => {
    logger.debug(`App rendered at ${new Date().toISOString()}`);
  }, []);
  
  return (
    <>
      <Head>
        <title>{env.NEXT_PUBLIC_APP_NAME}</title>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="description" content="A comprehensive meeting management application" />
      </Head>
      
      <DebugProvider>
        <ErrorBoundary onError={handleError}>
          <GoogleOAuthProvider clientId={process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID || ''}>
            <AuthProvider>
              <Component {...pageProps} />
            </AuthProvider>
          </GoogleOAuthProvider>
        </ErrorBoundary>
      </DebugProvider>
    </>
  );
}

export default MyApp; 