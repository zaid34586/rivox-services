import Head from 'next/head';
import Link from 'next/link';
import styles from '../styles/Home.module.css';

export default function Home() {
  const services = [
    { id: 'whatsapp', title: 'WhatsApp Automation', description: 'Auto-reply, booking, reminders, follow-up, review collection for local businesses.', price: '₹2,000–5,000/month' },
    { id: 'leadfinder', title: 'Lead Finder', description: 'Find international businesses (US/UK/CA/AU) by category and location.', price: '₹1,500/month' },
    { id: 'contentfactory', title: 'Content Factory', description: 'AI-generated posts, reels, stories, captions, hashtags.', price: '₹3,000/month' },
    { id: 'editor', title: 'Editor Agent', description: 'SEO optimization, A/B variants, accessibility, compliance.', price: 'Included with Content Factory' },
    { id: 'delivery', title: 'Delivery Agent', description: 'Scheduled publishing to IG, FB, YT, TT, LI, X with retry.', price: '₹1,000/month' },
  ];

  return (
    <>
      <Head>
        <title>Rivox Services</title>
        <meta name="description" content="Rivox Services Portal" />
        <link rel="icon" href="/favicon.ico" />
      </Head>

      <main className={styles.main}>
        <h1 className={styles.title}>
          Rivox Services Portal
        </h1>
        <p className={styles.description}>
          Browse and connect to automated services for your business.
        </p>

        <div className={styles.grid}>
          {services.map(service => (
            <Link key={service.id} href={`/service/${service.id}`} passHref>
              <a className={styles.card}>
                <h2>{service.title}</h2>
                <p>{service.description}</p>
                <p className={styles.price}>{service.price}</p>
              </a>
            </Link>
          ))}
        </div>
      </main>
    </>
  );
}
