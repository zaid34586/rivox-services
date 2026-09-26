import Link from 'next/link';
import glass from '../styles/glass.module.css';
import home from '../styles/Home.module.css';
import { contactWhatsApp } from '../data/services';

export default function ServiceDetail({ service }) {
  const waText = encodeURIComponent(
    `Hi Rivox! I'm interested in ${service.title} (${service.price}). Details chahiye.`
  );
  return (
    <div className={home.detail}>
      <div className={home.detailHead}>
        <div className={home.detailIcon}>{service.icon || '🤖'}</div>
        <div>
          <h2 className={home.detailTitle}>{service.title}</h2>
          <p className={home.detailTag}>{service.tagline}</p>
        </div>
      </div>

      <p className={home.detailDesc}>{service.description}</p>

      <div className={home.featureGrid}>
        {(service.features || []).map((f) => (
          <div className={home.feature} key={f.title}>
            <p className={home.featureTitle}>
              {f.icon} {f.title}
            </p>
            <p className={home.featureText}>{f.text}</p>
          </div>
        ))}
      </div>

      <div className={home.priceBox}>
        <div>
          <div className={home.priceVal}>{service.price}</div>
          <div className={home.priceNote}>{service.priceNote}</div>
        </div>
        <span className={`${glass.badge} ${glass.badgeGreen}`}>✓ Free setup</span>
      </div>

      <div className={home.ctaRow}>
        <a
          className={`${glass.btn} ${glass.btnWa}`}
          href={`https://wa.me/${contactWhatsApp}?text=${waText}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          💬 WhatsApp Contact
        </a>
        <Link href={`/enroll/${service.id}`} passHref>
          <a className={`${glass.btn} ${glass.btnPrimary}`}>⚡ Enroll Now →</a>
        </Link>
      </div>
    </div>
  );
}
