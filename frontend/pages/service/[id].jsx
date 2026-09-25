import { useState } from 'react';
import Head from 'next/head';
import styles from '../../styles/Home.module.css';
import Link from 'next/link';
import { services } from '../../data/services';

export default function Service({ service }) {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    businessId: '',
    name: '',
    category: '',
    timezone: 'Asia/Kolkata',
    workingHoursStart: '09:00',
    workingHoursEnd: '18:00',
    phoneNumber: '',
    details: {
      // For restaurant example
      specialties: '',
      opensAt: '',
      closesAt: '',
    }
  });
  const [status, setStatus] = useState('idle'); // idle, loading, success, error
  const [message, setMessage] = useState('');
  const [sessionValid, setSessionValid] = useState(null); // null = not checked, true/false
  const [qrCode, setQrCode] = useState(null);
  const [scanned, setScanned] = useState(false);

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setStatus('loading');
    setMessage('');

    try {
      // Step 1: Verify session if we have a businessId and claim to have scanned
      if (step === 2 && formData.businessId) {
        const verifyRes = await fetch(`/api/verify-session/${formData.businessId}`, {
          method: 'GET'
        });
        const verifyData = await verifyRes.json();
        setSessionValid(verifyData.valid);
        if (!verifyData.valid) {
          setStatus('error');
          setMessage(`Session invalid: ${verifyData.reason || 'Please scan the QR code and try again.'}`);
          return;
        }
      }

      // Step 2: Onboard the business
      const onboardRes = await fetch('/api/onboard', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          businessId: formData.businessId,
          name: formData.name,
          category: formData.category,
          timezone: formData.timezone,
          workingHoursStart: formData.workingHoursStart,
          workingHoursEnd: formData.workingHoursEnd
        })
      });
      const onboardData = await onboardRes.json();
      if (onboardData.success) {
        setStatus('success');
        setMessage('Business onboarded successfully! Your WhatsApp agent is now active.');
        // Optionally, we could reset the form or show next steps
      } else {
        setStatus('error');
        setMessage(onboardData.error || 'Failed to onboard business.');
      }
    } catch (err) {
      setStatus('error');
      setMessage('Network error. Please try again.');
      console.error(err);
    }
  };

  const getQRCode = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_BRIDGE_URL}/qr`);
      if (!res.ok) throw new Error('Failed to fetch QR');
      const blob = await res.blob();
      const reader = new FileReader();
      reader.onloadend = () => {
        setQrCode(reader.result);
      };
      reader.readAsDataURL(blob);
    } catch (err) {
      console.error('QR fetch error:', err);
      setMessage('Could not load QR code. Please ensure the bridge is running.');
    }
  };

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
    serviceContent = (
      <div className="service-content">
        {step === 1 && (
          <>
            <h2>Get Started with WhatsApp Automation</h2>
            <p className="mb-4">
              Connect your business WhatsApp number to automate customer interactions:
              auto-reply, booking, reminders, follow-ups, and review collection.
            </p>
            <div className="mb-4">
              <label htmlFor="businessId">Business ID (unique, e.g., restaurant_name)</label>
              <input
                id="businessId"
                type="text"
                name="businessId"
                value={formData.businessId || ''}
                onChange={handleChange}
                required
                className="input w-full mt-1"
                placeholder="e.g., my_restaurant"
              />
            </div>
            <div className="mb-4">
              <label htmlFor="phoneNumber">WhatsApp Number (with country code)</label>
              <input
                id="phoneNumber"
                type="tel"
                name="phoneNumber"
                value={formData.phoneNumber || ''}
                onChange={handleChange}
                required
                className="input w-full mt-1"
                placeholder="+919876543210"
              />
            </div>
            <button
              onClick={async () => {
                setStep(2);
                await getQRCode();
              }}
              disabled={step !== 1}
              className="btn btn-primary w-full"
            >
              Step 2: Scan QR Code
            </button>
          </>
        )}
        {step === 2 && (
          <>
            <h2>Scan QR Code to Link WhatsApp</h2>
            <p className="mb-4">
              Use your phone's WhatsApp to scan the QR code below:
              Go to WhatsApp Settings &gt; Linked Devices &gt; Link a Device.
            </p>
            {qrCode && (
              <div className="mb-4">
                <img src={qrCode} alt="WhatsApp QR Code" className="qr-code" />
              </div>
            )}
            {!qrCode && (
              <div className="mb-4">
                <p>Loading QR code...</p>
                <button onClick={getQRCode} className="btn btn-outline">
                  Retry
                </button>
              </div>
            )}
            <div className="mb-4">
              <label>
                <input
                  type="checkbox"
                  name="scanned"
                  checked={scanned}
                  onChange={e => setScanned(e.target.checked)}
                />
                I've scanned the QR code
              </label>
            </div>
            <div className="mb-4">
              {sessionValid === null && (
                <p>Click "Verify Session" after scanning to confirm connection.</p>
              )}
              {sessionValid === true && (
                <p className="text-success">Session verified! Your WhatsApp is now linked.</p>
              )}
              {sessionValid === false && (
                <p className="text-error">Session not valid. Please scan the QR code again.</p>
              )}
            </div>
            <div className="flex flex-col sm:flex-row gap-4">
              <button
                onClick={getQRCode}
                className="btn btn-outline flex-1"
              >
                Refresh QR
              </button>
              <button
                onClick={() => {
                  if (scanned) {
                    setStep(3);
                  } else {
                    setMessage('Please confirm you have scanned the QR code.');
                  }
                }}
                disabled={!scanned}
                className="btn btn-primary flex-1"
              >
                Step 3: Enter Business Details
              </button>
            </div>
          </>
        )}
        {step === 3 && (
          <>
            <h2>Business Details</h2>
            <p className="mb-4">
              Fill in your business information to customize the agent's behavior.
            </p>
            <div className="mb-4">
              <label htmlFor="name">Business Name</label>
              <input
                id="name"
                type="text"
                name="name"
                value={formData.name || ''}
                onChange={handleChange}
                required
                className="input w-full mt-1"
                placeholder="e.g., My Restaurant"
              />
            </div>
            <div className="mb-4">
              <label htmlFor="category">Business Category</label>
              <select
                id="category"
                name="category"
                value={formData.category || ''}
                onChange={handleChange}
                required
                className="select w-full mt-1"
              >
                <option value="">Select category</option>
                <option value="restaurant">Restaurant</option>
                <option value="salon">Salon / Spa</option>
                <option value="clinic">Clinic / Healthcare</option>
                <option value="retail">Retail Store</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="mb-4">
              <label htmlFor="timezone">Timezone</label>
              <input
                id="timezone"
                type="text"
                name="timezone"
                value={formData.timezone || 'Asia/Kolkata'}
                onChange={handleChange}
                className="input w-full mt-1"
                placeholder="Asia/Kolkata"
              />
            </div>
            <div className="mb-4">
              <label htmlFor="workingHoursStart">Working Hours Start</label>
              <input
                id="workingHoursStart"
                type="time"
                name="workingHoursStart"
                value={formData.workingHoursStart || '09:00'}
                onChange={handleChange}
                className="input w-full mt-1"
              />
            </div>
            <div className="mb-4">
              <label htmlFor="workingHoursEnd">Working Hours End</label>
              <input
                id="workingHoursEnd"
                type="time"
                name="workingHoursEnd"
                value={formData.workingHoursEnd || '18:00'}
                onChange={handleChange}
                className="input w-full mt-1"
              />
            </div>
            {/* Category-specific fields (example for restaurant) */}
            {formData.category === 'restaurant' && (
              <>
                <div className="mb-4">
                  <label htmlFor="specialties">Specialties (e.g., North Indian, Chinese)</label>
                  <input
                    id="specialties"
                    type="text"
                    name="specialties"
                    value={formData.details?.specialties || ''}
                    onChange={e => setFormData(prev => ({ ...prev, details: { ...prev.details, specialties: e.target.value } }))}
                    className="input w-full mt-1"
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="opensAt">Opening Time</label>
                  <input
                    id="opensAt"
                    type="time"
                    name="opensAt"
                    value={formData.details?.opensAt || ''}
                    onChange={e => setFormData(prev => ({ ...prev, details: { ...prev.details, opensAt: e.target.value } }))}
                    className="input w-full mt-1"
                  />
                </div>
                <div className="mb-4">
                  <label htmlFor="closesAt">Closing Time</label>
                  <input
                    id="closesAt"
                    type="time"
                    name="closesAt"
                    value={formData.details?.closesAt || ''}
                    onChange={e => setFormData(prev => ({ ...prev, details: { ...prev.details, closesAt: e.target.value } }))}
                    className="input w-full mt-1"
                  />
                </div>
              </>
            )}
            <button
              onClick={handleSubmit}
              disabled={status === 'loading'}
              className="btn btn-primary w-full"
            >
              {status === 'loading' ? 'Onboarding...' : 'Complete Setup'}
            </button>
            {status === 'success' && (
              <div className="mt-4 p-4 bg-green-50 border-l-4 border-green-500">
                <h3 className="text-green-800">Setup Complete!</h3>
                <p>
                  Your WhatsApp automation agent is now active. Customers can message your WhatsApp number
                  and receive automated replies. You can manage the agent via the Hermes dashboard.
                </p>
                <Link href="/" passThru>
                  <a className="btn btn-outline mt-2">Back to Home</a>
                </Link>
              </div>
            )}
            {status === 'error' && (
              <div className="mt-4 p-4 bg-red-50 border-l-4 border-red-500">
                <h3 className="text-red-800">Setup Failed</h3>
                <p className="text-red-600">{message}</p>
                <button
                  onClick={() => {
                    setStatus('idle');
                    setMessage('');
                  }}
                  className="btn btn-outline mt-2"
                >
                  Try Again
                </button>
              </div>
            )}
          </>
        )}
      </div>
    );
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
