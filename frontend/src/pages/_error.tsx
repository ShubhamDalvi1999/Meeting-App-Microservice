import React from 'react';
import { NextPage } from 'next';
import Head from 'next/head';
import Link from 'next/link';
import { useRouter } from 'next/router';
import logger from '@/utils/logger';

interface ErrorProps {
  statusCode?: number;
  message?: string;
  hasGetInitialPropsRun?: boolean;
  err?: Error;
}

/**
 * Custom Next.js error page that handles both 404s and other error codes.
 */
const ErrorPage: NextPage<ErrorProps> = ({ statusCode, message, hasGetInitialPropsRun, err }) => {
  const router = useRouter();
  
  // Log the error when component mounts
  React.useEffect(() => {
    // Only log if we have an actual error (skip 404s for non-existent routes)
    if (statusCode && statusCode !== 404) {
      logger.error(`Error page displayed with status: ${statusCode}, URL: ${router.asPath}`);
      
      if (err) {
        logger.error('Error details:', err);
      }
    }
  }, [statusCode, err, router.asPath]);

  // Handle 404 errors
  if (statusCode === 404) {
    return (
      <>
        <Head>
          <title>Page Not Found | Meeting App</title>
        </Head>
        <div className="error-page not-found">
          <div className="error-container">
            <h1>404</h1>
            <h2>Page Not Found</h2>
            <p>Sorry, we couldn't find the page you're looking for.</p>
            <div className="error-actions">
              <Link href="/" className="btn btn-primary">
                Go to Home
              </Link>
              <button 
                className="btn btn-secondary" 
                onClick={() => router.back()}
              >
                Go Back
              </button>
            </div>
          </div>
        </div>
      </>
    );
  }

  // Handle other errors
  return (
    <>
      <Head>
        <title>Error | Meeting App</title>
      </Head>
      <div className="error-page">
        <div className="error-container">
          <h1>{statusCode || 'Error'}</h1>
          <h2>Something went wrong</h2>
          <p>{message || 'An unexpected error occurred'}</p>
          
          {process.env.NODE_ENV === 'development' && err && (
            <details className="error-details">
              <summary>Error Details</summary>
              <pre>{err.message}</pre>
              <pre>{err.stack}</pre>
            </details>
          )}
          
          <div className="error-actions">
            <Link href="/" className="btn btn-primary">
              Go to Home
            </Link>
            <button 
              className="btn btn-secondary" 
              onClick={() => router.reload()}
            >
              Reload Page
            </button>
          </div>
        </div>
      </div>
    </>
  );
};

// This gets called on server-side errors
ErrorPage.getInitialProps = async ({ res, err, asPath }) => {
  const errorInitialProps: ErrorProps = {
    hasGetInitialPropsRun: true,
    statusCode: res?.statusCode || (err ? 500 : 404),
  };
  
  // Keep the original error for debugging in development
  if (process.env.NODE_ENV === 'development' && err) {
    errorInitialProps.err = err;
    errorInitialProps.message = err.message;
    
    // Log the error on the server side
    console.error(`Server-side error occurred on ${asPath}:`, err);
  }
  
  return errorInitialProps;
};

export default ErrorPage; 