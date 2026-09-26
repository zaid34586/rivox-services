import { useState, useEffect } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import glass from '../styles/glass.module.css';
import home from '../styles/Home.module.css';
import { services } from '../data/services';
import ServiceDetail from '../components/ServiceDetail';

export default function Home() {
  const [open, setOpen] = useState(false);
  const service = services[0];

  useEffect(() => {
    const onKey = (e) => {
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, []);

  return (
    <div className={glass.page}>
      <Head>
        <title>Rivox — WhatsApp AI Agent for your business</title>
        <meta
          name="description"
          content="Rivox WhatsApp AI Agent — 24/7 replies, bookings, orders & feedback automation for your business."
        />
      </Head>

      <div className={`${glass.orb} ${glass.orbA}`} />
      <div className={`${glass.orb} ${glass.orbB}`} />
      <div className={`${glass.orb} ${glass.orbC}`} />

      <header className={home.hero}>
        <div className={home.brandRow}>
          <span className={home.brandDot} />
          <h1 className={home.brand}>RIVOX</h1>
          <span className={home.brandDot} />
        </div>
        <p className={home.sub}>
          AI-powered services for your business. Scan, connect, and let automation
          handle customers 24/7.
        </p>
      </header>

      <main className={home.grid}>
        <div
          className={`${glass.glass} ${home.card}`}
          onClick={() => setOpen(true)}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => e.key === 'Enter' && setOpen(true)}
        >
          <div className={home.cardIcon}>{service.icon}</div>
          <h2 className={home.cardTitle}>{service.title}</h2>
          <p className={home.cardTag}>{service.tagline}</p>
          <div className={home.cardPriceRow}>
            <span className={home.cardPrice}>{service.price}</span>
            <span className={home.cardCta}>VIEW DETAILS →</span>
          </div>
        </div>
      </main>

      {open && (
        <div className={home.overlay} onClick={(e) => e.target === e.currentTarget && setOpen(false)}>
          <div className={`${glass.glass} ${home.modal}`}>
            <button className={home.closeBtn} onClick={() => setOpen(false)} aria-label="Close">
              ×
            </button>
            <ServiceDetail service={service} />
          </div>
        </div>
      )}

      <footer className={glass.footer}>
        © {new Date().getFullYear()} Rivox · <Link href="/service/whatsapp">WhatsApp AI Agent</Link>
      </footer>
    </div>
  );
}
