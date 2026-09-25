import { useState, useEffect, useRef } from 'react';

const BRIDGE_URL = process.env.NEXT_PUBLIC_BRIDGE_URL || 'http://51.21.162.170:8081';

export default function Onboarding() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    businessId: '',
    phoneNumber: '',
    name: '',
    category: '',
    timezone: 'Asia/Kolkata',
    workingHoursStart: '09:00',
    workingHoursEnd: '18:00',
    specialties: '',
    opensAt: '',
    closesAt: '',
    ownerWhatsApp: '',
    services: ['table_booking'],
  });
  const [status, setStatus] = useState('idle');
  const [message, setMessage] = useState('');
  const [qrCode, setQrCode] = useState(null);
  const [qrLoading, setQrLoading] = useState(false);
  const [sessionValid, setSessionValid] = useState(null);
  const [scanned, setScanned] = useState(false);
  const qrPollRef = useRef(null);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    if (type === 'checkbox') {
      const current = formData[name] || [];
      setFormData(prev => ({
        ...prev,
        [name]: checked ? [...current, value] : current.filter(v => v !== value),
      }));
    } else {
      setFormData(prev => ({ ...prev, [name]: type === 'checkbox' ? checked : value }));
    }
  };

  const apiCall = async (endpoint, options = {}) => {
    const res = await fetch(`${BRIDGE_URL}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);
    return data;
  };

  const fetchQR = async () => {
    setQrLoading(true);
    setQrCode(null);
    setSessionValid(null);
    try {
      const res = await fetch(`${BRIDGE_URL}/qr`);
      if (!res.ok) throw new Error('Failed to fetch QR');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      setQrCode(url);
      setQrLoading(false);
      startQRPolling();
    } catch (err) {
      setQrLoading(false);
      setMessage('Could not load QR code: ' + err.message);
    }
  };

  const startQRPolling = () => {
    if (qrPollRef.current) clearInterval(qrPollRef.current);
    qrPollRef.current = setInterval(async () => {
      try {
        const data = await apiCall(`/verify-session/${formData.businessId}`);
        if (data.valid) {
          clearInterval(qrPollRef.current);
          setSessionValid(true);
          setScanned(true);
        }
      } catch (e) { /* ignore */ }
    }, 3000);
  };

  const handleStep1Submit = async (e) => {
    e.preventDefault();
    setStatus('loading');
    setMessage('');

    const bizId = formData.businessId.trim().toLowerCase();
    const phone = formData.phoneNumber.trim();

    if (!/^[a-z0-9_]{3,50}$/.test(bizId)) {
      setStatus('error');
      setMessage('Business ID must be 3-50 chars: lowercase, numbers, underscore only');
      return;
    }
    if (!/^\+[1-9]\d{6,14}$/.test(phone.replace(/\s/g, ''))) {
      setStatus('error');
      setMessage('Enter valid WhatsApp number with country code (e.g., +919876543210)');
      return;
    }

    setFormData(prev => ({ ...prev, businessId: bizId, phoneNumber: phone }));
    setStatus('idle');
    setMessage('');
    setStep(2);
    await fetchQR();
  };

  const handleVerify = async () => {
    setStatus('loading');
    try {
      const data = await apiCall(`/verify-session/${formData.businessId}`);
      if (data.valid) {
        setStatus('idle');
        setStep(3);
      } else {
        setStatus('error');
        setMessage(data.reason || 'Session not valid. Please scan the QR code again.');
      }
    } catch (err) {
      setStatus('error');
      setMessage('Verification failed: ' + err.message);
    }
  };

  const handleStep3Submit = async (e) => {
    e.preventDefault();
    setStatus('loading');
    setMessage('');

    const payload = {
      businessId: formData.businessId,
      phoneNumber: formData.phoneNumber,
      name: formData.name,
      category: formData.category,
      timezone: formData.timezone,
      workingHoursStart: formData.workingHoursStart,
      workingHoursEnd: formData.workingHoursEnd,
      specialties: formData.specialties,
      opensAt: formData.opensAt,
      closesAt: formData.closesAt,
      ownerWhatsApp: formData.ownerWhatsApp,
      services: formData.services,
    };

    try {
      const data = await apiCall('/onboard', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      if (data.success) {
        setStatus('success');
        setMessage('Business onboarded successfully!');
      } else {
        setStatus('error');
        setMessage(data.error || 'Failed to onboard business');
      }
    } catch (err) {
      setStatus('error');
      setMessage('Onboarding failed: ' + err.message);
    }
  };

  useEffect(() => () => { if (qrPollRef.current) clearInterval(qrPollRef.current); }, []);

  const categoryLabels = {
    restaurant: '🍽️ Restaurant / Cafe',
    salon: '💇 Salon / Spa',
    clinic: '🏥 Clinic / Healthcare',
    retail: '🛍️ Retail Store',
    gym: '🏋️ Gym / Fitness',
    other: '📦 Other',
  };

  const serviceOptions = [
    { value: 'table_booking', label: '🍽️ Table Booking' },
    { value: 'food_order', label: '🛒 Food Order' },
    { value: 'party_booking', label: '🎂 Party / Birthday Booking' },
    { value: 'normal_chat', label: '💬 Normal Chat (FAQ)' },
  ];

  return (
    <div className={styles.container}>
      <div className={styles.stepIndicator}>
        <div className={`${styles.stepDot} ${step <= 1 ? (step > 1 ? styles.completed : styles.active) : ''}`} data-step="1"></div>
        <div className={`${styles.stepLine} ${step > 2 ? styles.completed : ''}`}></div>
        <div className={`${styles.stepDot} ${step === 2 ? styles.active : step > 2 ? styles.completed : ''}`} data-step="2"></div>
        <div className={`${styles.stepLine} ${step > 3 ? styles.completed : ''}`}></div>
        <div className={`${styles.stepDot} ${step === 3 ? styles.active : step > 3 ? styles.completed : ''}`} data-step="3"></div>
      </div>

      <div className={styles.card}>
        <div className={styles.cardHeader}>
          <h1>WhatsApp Automation</h1>
          <p>Connect your business WhatsApp to automate bookings, replies, reminders & reviews</p>
        </div>

        <div className={styles.cardBody}>
          {status === 'error' && (
            <div className={`${styles.alert} ${styles.error}`} role="alert">
              <svg className={styles.alertIcon} width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>
              <div>{message}</div>
            </div>
          )}

          {/* STEP 1 */}
          {step === 1 && (
            <form onSubmit={handleStep1Submit}>
              <h2 className={styles.stepTitle}>Step 1: Basic Info</h2>
              <p className={styles.stepDesc}>
                Enter your business ID and WhatsApp number to begin setup.
              </p>

              <div className={styles.formGroup}>
                <label htmlFor="businessId">Business ID <span className={styles.required}>*</span></label>
                <input
                  type="text" id="businessId" name="businessId" required
                  placeholder="e.g., spice_garden_delhi"
                  pattern="[a-z0-9_]{3,50}"
                  value={formData.businessId}
                  onChange={handleChange}
                  className={styles.input}
                />
                <small className={styles.helperText}>
                  Unique identifier for your business (used internally)
                </small>
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="phoneNumber">WhatsApp Number <span className={styles.required}>*</span></label>
                <input
                  type="tel" id="phoneNumber" name="phoneNumber" required
                  placeholder="+91 98765 43210"
                  value={formData.phoneNumber}
                  onChange={handleChange}
                  className={styles.input}
                />
                <small className={styles.helperText}>
                  Must be a valid WhatsApp number with country code
                </small>
              </div>

              <button type="submit" className={`${styles.btn} ${styles.btnPrimary}`} disabled={status === 'loading'}>
                {status === 'loading' ? <><span className={styles.spinner}></span> Loading...</> : 'Continue to QR Scan →'}
              </button>
            </form>
          )}

          {/* STEP 2 */}
          {step === 2 && (
            <>
              <h2 className={styles.stepTitle}>Step 2: Link WhatsApp</h2>
              <p className={styles.stepDesc}>
                Scan the QR code with your WhatsApp to connect your number.
              </p>

              <div className={styles.qrWrapper}>
                {qrLoading && (
                  <div className={styles.qrLoading}>
                    <div className={styles.spinner}></div>
                    <p>Generating QR code...</p>
                  </div>
                )}
                {!qrLoading && qrCode && (
                  <div>
                    <img src={qrCode} alt="WhatsApp QR Code" className={styles.qrImage} />
                    <p className={styles.qrStatus}>
                      {sessionValid ? '✓ Session verified! WhatsApp linked.' : 'Waiting for scan...'}
                    </p>
                  </div>
                )}
              </div>

              <div className={styles.qrInstructions}>
                <strong>How to scan:</strong>
                <ol>
                  <li>Open WhatsApp on your phone</li>
                  <li>Go to <strong>Settings → Linked Devices</strong></li>
                  <li>Tap <strong>Link a Device</strong></li>
                  <li>Point camera at the QR code above</li>
                </ol>
              </div>

              <div className={styles.checkboxGroup}>
                <input type="checkbox" id="scannedCheck" checked={scanned} onChange={e => setScanned(e.target.checked)} disabled={sessionValid} />
                <label htmlFor="scannedCheck">I've scanned the QR code with my phone</label>
              </div>

              <div className={styles.buttonGroup}>
                <button className={`${styles.btn} ${styles.btnOutline}`} onClick={fetchQR}>Refresh QR Code</button>
                <button className={`${styles.btn} ${styles.btnPrimary}`} onClick={handleVerify} disabled={!scanned || sessionValid || status === 'loading'}>
                  {status === 'loading' ? <><span className={styles.spinner}></span> Verifying...</> : sessionValid ? 'Verified ✓' : 'Verify & Continue →'}
                </button>
              </div>
            </>
          )}

          {/* STEP 3 */}
          {step === 3 && (
            <form onSubmit={handleStep3Submit}>
              <h2 className={styles.stepTitle}>Step 3: Business Details</h2>
              <p className={styles.stepDesc}>
                Customize your agent's behavior with your business information.
              </p>

              <div className={styles.formGroup}>
                <label htmlFor="bizName">Business Name <span className={styles.required}>*</span></label>
                <input type="text" id="bizName" name="name" required placeholder="e.g., Spice Garden Restaurant" value={formData.name} onChange={handleChange} className={styles.input} />
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="category">Category <span className={styles.required}>*</span></label>
                <select id="category" name="category" value={formData.category} onChange={handleChange} required className={styles.input}>
                  <option value="">Select category</option>
                  {Object.entries(categoryLabels).map(([val, label]) => (
                    <option key={val} value={val}>{label}</option>
                  ))}
                </select>
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label htmlFor="tz">Timezone</label>
                  <input type="text" id="tz" name="timezone" value={formData.timezone} readOnly className={styles.input} />
                </div>
                <div className={styles.formGroup}>
                  <label htmlFor="bizType">Business Type</label>
                  <input type="text" id="bizType" value={categoryLabels[formData.category] || ''} readOnly className={styles.input} style={{background:'var(--bg)'}} />
                </div>
              </div>

              <div className={styles.formRow}>
                <div className={styles.formGroup}>
                  <label htmlFor="openTime">Opens At</label>
                  <input type="time" id="openTime" name="workingHoursStart" value={formData.workingHoursStart} onChange={handleChange} className={styles.input} />
                </div>
                <div className={styles.formGroup}>
                  <label htmlFor="closeTime">Closes At</label>
                  <input type="time" id="closeTime" name="workingHoursEnd" value={formData.workingHoursEnd} onChange={handleChange} className={styles.input} />
                </div>
              </div>

              <div className={styles.formGroup}>
                <label htmlFor="ownerWhatsApp">Owner WhatsApp (for notifications) <span className={styles.required}>*</span></label>
                <input type="tel" id="ownerWhatsApp" name="ownerWhatsApp" required placeholder="+91 98765 43210" value={formData.ownerWhatsApp} onChange={handleChange} className={styles.input} />
                <small className={styles.helperText}>
                  Booking alerts & no-show notifications go here
                </small>
              </div>

              <div className={styles.formGroup}>
                <label>Enabled Services <span className={styles.required}>*</span></label>
                <div className={styles.serviceChecks}>
                  {serviceOptions.map(svc => (
                    <label key={svc.value} className={`${styles.serviceCheck} ${formData.services.includes(svc.value) ? styles.selected : ''}`}>
                      <input
                        type="checkbox"
                        name="services"
                        value={svc.value}
                        checked={formData.services.includes(svc.value)}
                        onChange={handleChange}
                      />
                      <span>{svc.label}</span>
                    </label>
                  ))}
                </div>
                <small className={styles.helperText}>
                  At least one service required
                </small>
              </div>

              {formData.category === 'restaurant' && (
                <div className={styles.restaurantFields}>
                  <h3 className={styles.sectionTitle}>Restaurant Details</h3>
                  <div className={styles.formGroup}>
                    <label htmlFor="specialties">Specialties</label>
                    <input type="text" id="specialties" name="specialties" placeholder="e.g., North Indian, Chinese, Mughlai" value={formData.specialties} onChange={handleChange} className={styles.input} />
                  </div>
                  <div className={styles.formRow}>
                    <div className={styles.formGroup}>
                      <label htmlFor="opensAt">Opening Time</label>
                      <input type="time" id="opensAt" name="opensAt" value={formData.opensAt} onChange={handleChange} className={styles.input} />
                    </div>
                    <div className={styles.formGroup}>
                      <label htmlFor="closesAt">Closing Time</label>
                      <input type="time" id="closesAt" name="closesAt" value={formData.closesAt} onChange={handleChange} className={styles.input} />
                    </div>
                  </div>
                </div>
              )}

              <button type="submit" className={`${styles.btn} ${styles.btnPrimary}`} disabled={status === 'loading'} style={{marginTop:'0.5rem'}}>
                {status === 'loading' ? <><span className={styles.spinner}></span> Onboarding...</> : 'Complete Setup'}
              </button>

              {status === 'success' && (
                <div className={styles.successState}>
                  <div className={styles.successIcon}>✓</div>
                  <h2 className={styles.successTitle}>Setup Complete!</h2>
                  <p className={styles.successDesc}>
                    Your WhatsApp automation agent is now active. Customers can message your WhatsApp number and receive instant automated replies for bookings, FAQs, and more.
                  </p>
                  <a href="/" className={`${styles.btn} ${styles.btnPrimary}`} style={{width:'auto',display:'inline-flex'}}>Back to Dashboard</a>
                </div>
              )}
            </form>
          )}
        </div>
      </div>

      <div className={styles.footer}>
        Powered by <a href="https://github.com/zaid34586/rivox-services">Rivox Services</a> &bull; Agent runs on Hermes (AWS)
      </div>
    </div>
  );
}