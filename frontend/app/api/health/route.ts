// Health check endpoint for AWS App Runner
// This endpoint is used by App Runner to verify the application is running correctly

import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Basic health check - can be extended to check database connections, etc.
    const healthStatus = {
      status: 'healthy',
      timestamp: new Date().toISOString(),
      service: 'Document Intelligence Frontend',
      version: process.env.NEXT_PUBLIC_APP_VERSION || '1.0.0',
      environment: process.env.NODE_ENV || 'development',
      uptime: process.uptime(),
      memory: {
        used: Math.round(process.memoryUsage().heapUsed / 1024 / 1024),
        total: Math.round(process.memoryUsage().heapTotal / 1024 / 1024),
        rss: Math.round(process.memoryUsage().rss / 1024 / 1024)
      }
    };

    return NextResponse.json(healthStatus, { status: 200 });
  } catch (error) {
    console.error('Health check failed:', error);
    
    return NextResponse.json(
      { 
        status: 'unhealthy', 
        timestamp: new Date().toISOString(),
        error: error instanceof Error ? error.message : 'Unknown error'
      }, 
      { status: 500 }
    );
  }
}

// Support for HEAD requests (some load balancers prefer HEAD for health checks)
export async function HEAD() {
  return new Response(null, { status: 200 });
}
