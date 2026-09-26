import { useState, useEffect, useRef, useCallback } from 'react';
import Head from 'next/head';
import Link from 'next/link';
import glass from '../../styles/glass.module.css';
import styles from '../../styles/Enroll.module.css';
import { services, contactWhatsApp, UPI_ID, UPI_AMOUNT } from '../../data/services';

const svc = services[0];

const STEPS = [
  { n: 1, label: 'Connect' },
  { n: 2, label: 'Scan QR' },
  { n: 3, label: 'Details' },
  { n: 4, label: 'Test & Pay' },
];

function normalizePhone(raw) {
  const d = (raw || '').replace(/[^\d+]/g, '').replace(/\+/g, '');
  let p = d;
  if (p.length === 10) p = '91' + p;
  if (!/^[1-9]\d{9,13}$/.test(p)) return null;
  if (p.length !== 12) return null;
  return '+' + p;
}

function slugify(s) {
  return (s || '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_+|_+$/g, '')
    .slice(0, 36);
}

async function apiCall(url, options = {}) {
  const res = await fetch(url, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...(options.headers || {}) },
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
  return data;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

export default function EnrollWhatsapp() {
  const [step, setStep] = useState(1);
  const [phoneRaw, setPhoneRaw] = useState('');
  const [phone, setPhone] = useState('');
  const [error, setError] = useState('');

  const [qrLoading, setQrLoading] = useState(false);
  const [qrUrl, setQrUrl] = useState(null);
  const [qrMessage, setQrMessage] = useState('');
  const [scanning, setScanning] = useState(false);

  const [connected, setConnected] = useState(false);
  const [leadName, setLeadName] = useState('');
  const [businessName, setBusinessName] = useState('');
  const [category, setCategory] = useState('');
  const [categoryOther, setCategoryOther] = useState('');
  const [address, setAddress] = useState('');
  const [about, setAbout] = useState('');
  const [chosen, setChosen] = useState([]);
  const [customOn, setCustomOn] = useState(false);
  const [customService, setCustomService] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const [finalBusinessId, setFinalBusinessId] = useState('');
  const [leadStatus, setLeadStatus] = useState('pending');
  const [copied, setCopied] = useState(false);

  const pollRef = useRef(null);
  const statusRef = useRef(null);

  const clearPoll = () => {
    if (pollRef.current) {
      clearInterval(pollRef.current);
      pollRef.current = null;
    }
  };
  const clearStatus = () => {
    if (statusRef.current) {
      clearInterval(statusRef.current);
      statusRef.current = null;
    }
  };

  useEffect(() => () => {
    clearPoll();
    clearStatus();
    if (qrUrl) URL.revokeObjectURL(qrUrl);
  }, []);

  const fetchQR = useCallback(async () => {
    setQrLoading(true);
    setQrMessage('');
    try {
      if (qrUrl) URL.revokeObjectURL(qrUrl);
      setQrUrl(null);
      let ok = false;
      for (let i = 0; i < 7 && !ok; i++) {
        const res = await fetch('/api/qr');
        if (res.ok) {
          const blob = await res.blob();
          if (blob.size > 500) {
            setQrUrl(URL.createObjectURL(blob));
            ok = true;
            break;
          }
        }
        await sleep(1300);
      }
      if (!ok) setQrMessage('QR abhi ready nahi hai — thodi der baad Refresh dabao.');
    } catch (e) {
      setQrMessage('QR load nahi hua: ' + e.message);
    }
    setQrLoading(false);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [qrUrl]);

  const startPolling = useCallback((e164) => {
    clearPoll();
    setScanning(true);
    pollRef.current = setInterval(async () => {
      try {
        const data = await apiCall(`/api/verify-phone?phone=${encodeURIComponent(e164)}`);
        if (data.valid) {
          clearPoll();
          setScanning(false);
          setConnected(true);
          setStep((s) => (s === 2 ? 3 : s));
        }
      } catch (e) {
        /* keep polling */
      }
    }, 3000);
  }, []);

  const handleConnect = async (e) => {
    e.preventDefault();
    setError('');
    const e164 = normalizePhone(phoneRaw);
    if (!e164) {
      setError('Sahi WhatsApp number daalo — 10 digit, country code ke saath (e.g. 9876543210).');
      return;
    }
    setPhone(e164);
    setQrLoading(true);
    setStep(2);
    try {
      await apiCall('/api/reset-session', { method: 'POST', body: JSON.stringify({ phone: e164 }) });
    } catch (err) {
      setError('Session reset fail: ' + err.message);
      setStep(1);
      setQrLoading(false);
      return;
    }
    setQrLoading(false);
    await fetchQR();
    startPolling(e164);
  };

  const refreshQR = async () => {
    setError('');
    try {
      await apiCall('/api/reset-session', { method: 'POST', body: JSON.stringify({ phone }) });
    } catch (err) {
      setError('Refresh fail: ' + err.message);
      return;
    }
    await fetchQR();
    startPolling(phone);
  };

  const toggleService = (value) => {
    setChosen((prev) => (prev.includes(value) ? prev.filter((v) => v !== value) : [...prev, value]));
  };

  const makeBusinessId = () => {
    const slug = slugify(businessName);
    const tail = (phone || '').replace(/\D/g, '').slice(-4) || '0000';
    let id = slug ? `${slug}_${tail}` : `biz_${tail}`;
    if (id.length < 3) id = `biz_${tail}`;
    if (!/^[a-z0-9_]+$/.test(id)) id = id.replace(/[^a-z0-9_]/g, '');
    return id.slice(0, 48);
  };

  const submitForm = async (e) => {
    e.preventDefault();
    setError('');
    if (!leadName.trim()) return setError('Apna naam daalo.');
    if (!businessName.trim()) return setError('Business ka naam daalo.');
    if (!category) return setError('Business type choose karo.');
    if (category === 'other' && !categoryOther.trim()) return setError('Other type likho.');
    if (chosen.length === 0 && !customOn) return setError('Kam se kam ek service choose karo.');
    if (customOn && !customService.trim()) return setError('Custom service likho.');

    const businessId = makeBusinessId();
    const servicesList = [...chosen];
    if (customOn && servicesList.length === 0) servicesList.push('normal_chat');

    const payload = {
      businessId,
      phoneNumber: phone,
      name: businessName.trim(),
      category: category === 'other' ? 'other' : category,
      categoryOther: categoryOther.trim(),
      timezone: 'Asia/Kolkata',
      workingHoursStart: '09:00',
      workingHoursEnd: '18:00',
      specialties: about.trim(),
      ownerWhatsApp: phone,
      services: servicesList.length ? servicesList : ['normal_chat'],
      leadName: leadName.trim(),
      address: address.trim(),
      customNote: customOn ? customService.trim() : '',
      source: 'portal_v2',
    };

    setSubmitting(true);
    try {
      const data = await apiCall('/api/onboard', { method: 'POST', body: JSON.stringify(payload) });
      if (data.success) {
        setFinalBusinessId(data.businessId || businessId);
        setStep(4);
        startStatusPoll(data.businessId || businessId);
      } else {
        setError(data.error || 'Setup fail — try again.');
      }
    } catch (err) {
      setError('Setup fail: ' + err.message);
    }
    setSubmitting(false);
  };

  const startStatusPoll = (bid) => {
    clearStatus();
    const check = async () => {
      try {
        const data = await apiCall(`/api/lead-status/${encodeURIComponent(bid)}`);
        if (data.payment && data.payment.status === 'paid') {
          setLeadStatus('paid');
          clearStatus();
        } else {
          setLeadStatus('pending');
        }
      } catch (e) {
        /* keep trying */
      }
    };
    check();
    statusRef.current = setInterval(check, 8000);
  };

  const copyUpi = async () => {
    try {
      await navigator.clipboard.writeText(UPI_ID);
      setCopied(true);
      setTimeout(() => setCopied(false), 1800);
    } catch (e) {
      /* ignore */
    }
  };

  const stepClass = (n) => {
    if (step > n) return `${styles.stepItem} ${styles.stepDone}`;
    if (step === n) return `${styles.stepItem} ${styles.stepActive}`;
    return styles.stepItem;
  };

  const waPaymentText = encodeURIComponent(
    `Payment screenshot 👍 — businessId: ${finalBusinessId || '(setup)'}`
  );

  return (
    <div className={glass.page}>
      <Head>
        <title>Enroll — WhatsApp AI Agent | Rivox</title>
        <meta name="description" content="Connect your WhatsApp and start your AI agent in minutes." />
      </Head>

      <div className={`${glass.orb} ${glass.orbA}`} />
      <div className={`${glass.orb} ${glass.orbB}`} />

      <header className={styles.head}>
        <Link href="/">
          <a className={styles.backLink}>← Back to Rivox</a>
        </Link>
        <span className={`${glass.badge}`}>⚡ {svc.title}</span>
        <h1 className={styles.title}>Connect & Enroll</h1>
        <p className={styles.priceLine}>{svc.price}</p>
        <p className={styles.priceNote}>{svc.priceNote}</p>
      </header>

      <div className={styles.stepper}>
        {STEPS.map((s, i) => (
          <div key={s.n} style={{ display: 'contents' }}>
            <div className={stepClass(s.n)}>
              <div className={styles.stepBubble}>{step > s.n ? '✓' : s.n}</div>
              <div className={styles.stepLabel}>{s.label}</div>
            </div>
            {i < STEPS.length - 1 && (
              <div className={`${styles.stepLine} ${step > s.n ? styles.stepLineDone : ''}`} />
            )}
          </div>
        ))}
      </div>

      <div className={`${glass.glass} ${styles.panel}`}>
        {error && <div className={`${glass.alert} ${glass.alertError}`}>{error}</div>}

        {/* STEP 1 — CONNECT NUMBER */}
        {step === 1 && (
          <>
            <h2 className={styles.panelTitle}>Apna WhatsApp number daalo</h2>
            <p className={styles.panelDesc}>
              Jis WhatsApp account ko connect karna hai wahi number daalo — usi pe QR scan
              hoga aur agent usi number pe customers ko reply karega.
            </p>
            <form onSubmit={handleConnect}>
              <div className={styles.field}>
                <label className={glass.label} htmlFor="phone">WhatsApp Number</label>
                <input
                  id="phone"
                  className={glass.input}
                  type="tel"
                  inputMode="tel"
                  placeholder="98765 43210"
                  value={phoneRaw}
                  onChange={(e) => setPhoneRaw(e.target.value)}
                  autoFocus
                />
                <p className={glass.help}>10 digit number — country code apne aap +91 lagega.</p>
              </div>
              <button className={`${glass.btn} ${glass.btnPrimary} ${glass.btnBlock}`} type="submit">
                {qrLoading ? <span className={glass.spinner} /> : 'Get QR Code →'}
              </button>
            </form>
          </>
        )}

        {/* STEP 2 — QR */}
        {step === 2 && (
          <>
            <h2 className={styles.panelTitle}>QR scan karo</h2>
            <p className={styles.panelDesc}>
              Apne <strong>{phone}</strong> wale WhatsApp pe scan karo.
            </p>
            {error && <div className={`${glass.alert} ${glass.alertError}`}>{error}</div>}
            <div className={styles.qrWrap}>
              {qrLoading ? (
                <p className={styles.qrStatus}>
                  <span className={glass.spinner} /> QR generate ho raha hai…
                </p>
              ) : qrUrl ? (
                <img className={styles.qrImage} src={qrUrl} alt="WhatsApp QR" />
              ) : (
                <p className={styles.qrStatus}>⚠ {qrMessage || 'QR load ho raha hai…'}</p>
              )}

              <ol className={styles.qrSteps}>
                <li>Apne phone kholo → <strong>WhatsApp</strong></li>
                <li><strong>Settings → Linked Devices → Link a Device</strong></li>
                <li>Upar wala QR scan karo</li>
              </ol>

              <p className={styles.qrStatus}>
                {connected ? (
                  <span className={`${glass.badge} ${glass.badgeGreen}`}>✓ Connected! Form khul raha hai…</span>
                ) : scanning ? (
                  <><span className={styles.dotPulse} /> Scan ka intezaar hai — connected hone par form apne aap khulega…</>
                ) : (
                  <span className={glass.badge}>QR expire ho gaya? Refresh karo</span>
                )}
              </p>

              <button className={`${glass.btn} ${glass.btnGhost}`} onClick={refreshQR} disabled={qrLoading}>
                ↻ Refresh QR
              </button>
            </div>
          </>
        )}

        {/* STEP 3 — FORM */}
        {step === 3 && (
          <>
            <div className={styles.connectedBar}>✓ WhatsApp connected — {phone}</div>
            <h2 className={styles.panelTitle}>Business details bharo</h2>
            <p className={styles.panelDesc}>
              Ye details agent ko milengi — usi se aapke customers ko sahi jawab, booking aur
              updates jayengi.
            </p>
            <form onSubmit={submitForm}>
              <div className={styles.row2}>
                <div className={styles.field}>
                  <label className={glass.label} htmlFor="leadName">Aapka Naam *</label>
                  <input
                    id="leadName" className={glass.input} placeholder="Mohd Zaid"
                    value={leadName} onChange={(e) => setLeadName(e.target.value)}
                  />
                </div>
                <div className={styles.field}>
                  <label className={glass.label} htmlFor="businessName">Business Naam *</label>
                  <input
                    id="businessName" className={glass.input} placeholder="Spice Garden"
                    value={businessName} onChange={(e) => setBusinessName(e.target.value)}
                  />
                </div>
              </div>

              <div className={styles.field}>
                <label className={glass.label} htmlFor="category">Business Type *</label>
                <select
                  id="category" className={`${glass.select} ${glass.input}`}
                  value={category} onChange={(e) => setCategory(e.target.value)}
                >
                  <option value="">— Choose —</option>
                  {svc.categoryOptions.map((c) => (
                    <option key={c.value} value={c.value}>{c.label}</option>
                  ))}
                </select>
              </div>

              {category === 'other' && (
                <div className={styles.field}>
                  <label className={glass.label} htmlFor="categoryOther">Apna type likho *</label>
                  <input
                    id="categoryOther" className={glass.input} placeholder="e.g. Pet Grooming"
                    value={categoryOther} onChange={(e) => setCategoryOther(e.target.value)}
                  />
                </div>
              )}

              <div className={styles.row2}>
                <div className={styles.field}>
                  <label className={glass.label} htmlFor="address">Address (optional)</label>
                  <input
                    id="address" className={glass.input} placeholder="Shop / area / city"
                    value={address} onChange={(e) => setAddress(e.target.value)}
                  />
                </div>
                <div className={styles.field}>
                  <label className={glass.label} htmlFor="about">Aapki services / menu (optional)</label>
                  <input
                    id="about" className={glass.input} placeholder="e.g. Hair cut, Facial…"
                    value={about} onChange={(e) => setAbout(e.target.value)}
                  />
                </div>
              </div>

              <div className={styles.field}>
                <label className={glass.label}>Agent kya kare? * (choose services)</label>
                <div className={styles.pills}>
                  {svc.serviceOptions.map((s) => (
                    <button
                      key={s.value}
                      type="button"
                      className={`${styles.pill} ${chosen.includes(s.value) ? styles.pillOn : ''}`}
                      onClick={() => toggleService(s.value)}
                    >
                      {s.label}
                    </button>
                  ))}
                  <button
                    type="button"
                    className={`${styles.pill} ${customOn ? styles.pillOn : ''}`}
                    onClick={() => setCustomOn((v) => !v)}
                  >
                    ✎ Other (type yourself)
                  </button>
                </div>
              </div>

              {customOn && (
                <div className={styles.field}>
                  <label className={glass.label} htmlFor="customService">Apni service likho</label>
                  <input
                    id="customService" className={glass.input}
                    placeholder="e.g. Appointment booking for hair coloring"
                    value={customService} onChange={(e) => setCustomService(e.target.value)}
                  />
                  <p className={glass.help}>
                    Custom service ke saath FAQ auto-reply bhi on ho jayega — final setup hum
                    aapke saath confirm karenge.
                  </p>
                </div>
              )}

              <div className={styles.field}>
                <label className={glass.label}>Aapka Business ID (auto)</label>
                <div className={styles.idPreview}>{makeBusinessId()}</div>
                <p className={glass.help}>Internally use hota hai — yaad rakhne ki zaroorat nahi.</p>
              </div>

              <button
                className={`${glass.btn} ${glass.btnPrimary} ${glass.btnBlock}`}
                type="submit"
                disabled={submitting}
              >
                {submitting ? <span className={glass.spinner} /> : 'Setup Shuru Karo →'}
              </button>
            </form>
          </>
        )}

        {/* STEP 4 — DONE + TEST + PAY */}
        {step === 4 && (
          <div className={styles.center}>
            <div className={styles.successIcon}>✓</div>
            <h2 className={styles.panelTitle}>Setup shuru ho gaya! 🎉</h2>
            <p className={styles.panelDesc}>
              Business ID: <strong>{finalBusinessId}</strong> — agent abhi start ho raha hai
              (30–60 second).
            </p>

            <div className={styles.testBox}>
              <strong>🧪 Ab TEST karo:</strong>
              <br />
              Kisi <strong>doosre phone / doosre WhatsApp number</strong> se apne connected
              WhatsApp number pe message bhejo — booking, order ya koi bhi sawaal likho. Agent
              turant jawab dega. <em>(Apne hi number pe self-chat se nahi chalega.)</em>
            </div>

            <div className={styles.payBox}>
              <p className={styles.payTitle}>💳 Payment — service ACTIVE karne ke liye</p>
              <div className={styles.upiRow}>
                <span className={styles.upiVal}>{UPI_ID}</span>
                <button className={styles.copyBtn} onClick={copyUpi}>
                  {copied ? '✓ Copied' : 'Copy UPI'}
                </button>
              </div>
              <div className={styles.upiRow}>
                <span className={styles.upiVal}>Amount: ₹{UPI_AMOUNT}</span>
                <span className={`${glass.badge} ${glass.badgeAmber}`}>month 1</span>
              </div>
              <ol className={styles.paySteps}>
                <li>UPI pe <strong>₹{UPI_AMOUNT}</strong> bhejo (<strong>{UPI_ID}</strong>)</li>
                <li>Payment ka <strong>screenshot</strong> neeche button se WhatsApp pe bhejo</li>
                <li>Hum approve karte hi service <strong>ACTIVE</strong> ✅</li>
              </ol>
              <a
                className={`${glass.btn} ${glass.btnWa} ${glass.btnBlock}`}
                href={`https://wa.me/${contactWhatsApp}?text=${waPaymentText}`}
                target="_blank"
                rel="noopener noreferrer"
              >
                📸 Payment Screenshot WhatsApp pe Bhejo
              </a>

              <div className={styles.statusRow}>
                <span className={styles.statusLabel}>Service status:</span>
                {leadStatus === 'paid' ? (
                  <span className={`${glass.badge} ${glass.badgeGreen}`}>✅ SERVICE ACTIVE</span>
                ) : (
                  <span className={`${glass.badge} ${glass.badgeAmber}`}>⏳ Payment pending</span>
                )}
              </div>
            </div>

            <div style={{ marginTop: 20 }}>
              <Link href="/">
                <a className={`${glass.btn} ${glass.btnGhost}`}>← Rivox Home</a>
              </Link>
            </div>
          </div>
        )}
      </div>

      <footer className={glass.footer}>
        © {new Date().getFullYear()} Rivox · Need help?{' '}
        <a
          href={`https://wa.me/${contactWhatsApp}`}
          target="_blank"
          rel="noopener noreferrer"
        >
          WhatsApp us
        </a>
      </footer>
    </div>
  );
}
