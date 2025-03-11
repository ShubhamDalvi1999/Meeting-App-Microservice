const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  
  // Disable TypeScript checking during build
  typescript: {
    // !! WARN !!
    // Dangerously allow production builds to successfully complete even if
    // your project has type errors.
    // !! WARN !!
    ignoreBuildErrors: true,
  },
  
  // Disable ESLint during build
  eslint: {
    // Warning: This allows production builds to successfully complete even if
    // your project has ESLint errors.
    ignoreDuringBuilds: true,
  },
  
  // Disable static generation and export
  output: 'standalone',
  
  // Configure to avoid static generation issues
  experimental: {
    // Turn off static optimization for pages that use getServerSideProps
    serverComponents: false
  },
  
  // Server options to ensure binding to all network interfaces
  serverRuntimeConfig: {
    // Will only be available on the server side
    hostname: '0.0.0.0',
  },
  
  // Default environment variables
  env: {
    // App information
    NEXT_PUBLIC_APP_NAME: 'Meeting App',
    NEXT_PUBLIC_APP_VERSION: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
    
    // API endpoints with defaults
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000',
    NEXT_PUBLIC_AUTH_URL: process.env.NEXT_PUBLIC_AUTH_URL || 'http://localhost:5001',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:3001',
    
    // Feature flags
    NEXT_PUBLIC_ENABLE_ANALYTICS: process.env.NEXT_PUBLIC_ENABLE_ANALYTICS || 'false',
    NEXT_PUBLIC_ENABLE_DEBUG_TOOLS: process.env.NODE_ENV !== 'production' ? 'true' : (process.env.NEXT_PUBLIC_ENABLE_DEBUG_TOOLS || 'false'),
    
    // Timeouts and limits
    NEXT_PUBLIC_API_TIMEOUT_MS: process.env.NEXT_PUBLIC_API_TIMEOUT_MS || '30000',
    NEXT_PUBLIC_WS_RECONNECT_INTERVAL_MS: process.env.NEXT_PUBLIC_WS_RECONNECT_INTERVAL_MS || '5000',
    NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB: process.env.NEXT_PUBLIC_MAX_UPLOAD_SIZE_MB || '5',
  },
  
  // Images configuration
  images: {
    domains: ['localhost'],
  },
  
  // Enable SWC minification
  swcMinify: true,
  
  // Disable source maps in production
  productionBrowserSourceMaps: false,
  
  // Configure webpack
  webpack: (config, { dev, isServer }) => {
    // External dependencies
    config.externals = [...config.externals, { 'simple-peer': 'SimplePeer' }];
    
    // Path aliases
    config.resolve = {
      ...config.resolve,
      alias: {
        ...config.resolve.alias,
        '@': path.join(__dirname, 'src'),
      },
    };
    
    // Example: Add environment variable injection through DefinePlugin
    // if (dev) {
    //   const webpack = require('webpack');
    //   config.plugins.push(
    //     new webpack.DefinePlugin({
    //       'process.env.APP_BUILD_TIME': JSON.stringify(new Date().toISOString()),
    //     })
    //   );
    // }
    
    return config;
  },
  
  // Header configurations
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-XSS-Protection',
            value: '1; mode=block',
          },
        ],
      },
      {
        source: '/:path*',
        headers: [
          { 
            key: 'Access-Control-Allow-Origin', 
            value: process.env.NODE_ENV === 'development' 
              ? 'http://localhost:5000' 
              : 'http://api.meeting-app.local' 
          },
          { key: 'Access-Control-Allow-Methods', value: 'GET,OPTIONS,PATCH,DELETE,POST,PUT' },
          { key: 'Access-Control-Allow-Headers', value: 'X-Requested-With, Content-Type, Authorization' },
          { key: 'Access-Control-Allow-Credentials', value: 'true' }
        ],
      },
    ];
  },
}

module.exports = nextConfig 