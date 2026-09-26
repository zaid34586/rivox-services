import Head from 'next/head';
import Link from 'next/link';
import glass from '../../styles/glass.module.css';
import home from '../../styles/Home.module.css';
import { services } from '../../data/services';
import ServiceDetail from '../../components/ServiceDetail';

export default function Service({ service }) {
  if (!service) {
    return (
      <div className={glass.page}>
        <div className={glass.wrap} style={{ paddingTop: 80, textAlign: 'center' }}>
          <h1 className={home.detailTitle}>Service not found</h1>
          <div style={{ marginTop: 24 }}>
            <Link href="/">
              <a className={`${glass.btn} ${glass.btnPrimary}`}>← Back to Rivox</a>
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={glass.page}>
      <Head>
        <title>{service.title} — Rivox</title>
        <meta name="description" content={service.tagline || service.description} />
      </Head>

      <div className={`${glass.orb} ${glass.orbA}`} />
      <div className={`${glass.orb} ${glass.orbB}`} />

      <div className={glass.wrap} style={{ paddingTop: 46 }}>
        <Link href="/">
          <a className={home.backLink}>← Back to Rivox</a>
        </Link>
        <div className={glass.glass} style={{ position: 'relative', zIndex: 1 }}>
          <ServiceDetail service={service} />
        </div>
      </div>

      <footer className={glass.footer}>© {new Date().getFullYear()} Rivox</footer>
    </div>
  );
}

export async function getServerSideProps(context) {
  const { id } = context.params;
  const service = services.find((s) => s.id === id) || null;
  return { props: { service } };
}
