import { useState } from 'react';
import Head from 'next/head';
import styles from '../../styles/Home.module.css';
import Link from 'next/link';
import { services } from '../../data/services';
import Onboarding from '../../components/Onboarding';

export default function Service({ service }) {
  if (!service) {
    return (
      <div className="service-content">
        <p>Service not found.</p>
        <Link href="/">Back to services</Link>
      </div>
    );
  }

  // Service-specific rendering
  let serviceContent;
  if (service.id === 'whatsapp') {
    serviceContent = <Onboarding />;
  } else {
    // Generic service placeholder
    serviceContent = (
      <div className="service-content">
        <h2>{service.title}</h2>
        <p>{service.description}</p>
        <p><strong>Price:</strong> {service.price}</p>
        <p className="mt-4">
          This service is currently in development. Please check back later.
        </p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Head>
        <title>{service.title} - Rivox Services</title>
        <meta name="description" content={service.description} />
      </Head>
      <main className="container mx-auto px-4 py-8">
        <div className="max-w-3xl mx-auto">
          <nav className="mb-6 flex items-center space-x-4">
            <Link href="/" passThru>
              <a className="text-sm text-gray-600 hover:text-gray-900">← Back to Services</a>
            </Link>
            <h1 className="text-2xl font-bold text-gray-900 flex-1">{service.title}</h1>
          </nav>

          <div className="bg-white rounded-xl shadow-md overflow-hidden">
            <div className="px-6 pt-6">
              {serviceContent}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export async function getServerSideProps(context) {
  const { id } = context.params;
  const service = services.find((s) => s.id === id) || null;
  return { props: { service } };
}
