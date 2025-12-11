import React from 'react';
import { useNavigate } from 'react-router-dom';

import Header from '../components/common/Header';
import { useAuth } from '../contexts/AuthContext';

const Home = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen flex flex-col">
      <Header
        title="AWS Cloud Health Dashboard"
        showNavigation={false}
      />

      <main className="flex-1">
        {/* Cosmic Hero Section */}
        <section className="hero">
          <div className="container">
            <div className="badge mb-6 animate-fade-in">
              <span className="text-cosmic-txt-2">New Features Available</span>
            </div>
            <h1 className="hero-title">
              AWS Cloud Health
              <br />
              Dashboard
            </h1>
            <p className="hero-subtitle">
              Monitor your cloud infrastructure with real-time insights, performance metrics, 
              and intelligent alerts in a beautiful cosmic interface.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center mt-8">
              <button
                className="btn btn-primary px-8 py-3 animate-float"
                onClick={() => navigate('/dashboard')}
              >
                View Dashboard
              </button>
            </div>
            
            {/* Trusted by section */}
            <div className="mt-16 pt-8 pb-10 border-t border-cosmic-border/30">
              <p className="text-cosmic-muted text-sm mb-6">Trusted by leading organizations</p>
              <div className="flex flex-wrap justify-center items-center gap-8 opacity-60">
                <div className="text-cosmic-txt-2 font-semibold">AWS</div>
                <div className="text-cosmic-txt-2 font-semibold">Microsoft</div>
                <div className="text-cosmic-txt-2 font-semibold">Google Cloud</div>
                <div className="text-cosmic-txt-2 font-semibold">IBM</div>
                <div className="text-cosmic-txt-2 font-semibold">Oracle</div>
              </div>
            </div>
          </div>
        </section>

        {/* Developer Team Section */}
        <section className="container mx-auto px-6 mt-[140px] sm:mt-[160px] pb-20 mb-20 lg:mb-28">
          <div className="max-w-3xl mx-auto text-center space-y-3 mb-14">
            <p className="text-xs uppercase tracking-[0.35em] text-cosmic-muted">
              THE TEAM BEHIND THE DASHBOARD
            </p>
            <h2 className="text-3xl sm:text-4xl font-bold text-cosmic-txt-1">
              Meet the Developers
            </h2>
            <p className="text-sm sm:text-base text-cosmic-txt-2 leading-relaxed">
              A small but passionate team of cloud enthusiasts and frontend engineers
              who designed and built this AWS Cloud Health experience.
            </p>
          </div>

          <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4 justify-items-center">
            {[
              { name: 'Developer 1', role: 'Cloud / Backend Engineer / Project Manager', image: '/dev_pic1.jpg' },
              { name: 'Developer 2', role: 'Frontend / DevOps / Team Leader / Backend Engineer', image: '/dev_pic2.jpg' },
              { name: 'Developer 3', role: 'Backend Engineer / Infrastructure / Tester', image: '/dev_pic3.jpg' },
              { name: 'Developer 4', role: 'QA / Frontend / UI Engineer', image: '/dev_pic4.jpg' },
            ].map((dev, idx) => (
              <div
                key={idx}
                className="w-full max-w-xs bg-cosmic-card border border-cosmic-border/60 rounded-2xl p-6 shadow-cosmic-soft hover:shadow-cosmic-glow transition-transform duration-200 hover:-translate-y-1 backdrop-blur-md"
              >
                <div className="flex flex-col items-center text-center space-y-4">
                  <img
                    src={dev.image}
                    alt={dev.name}
                    className={`w-28 h-28 rounded-3xl object-cover shadow-lg shadow-blue-500/40 border border-cosmic-border/50 ${
                      dev.name === 'Developer 3' ? 'object-top' : 'object-center'
                    }`}
                  />

                  <div>
                    <h3 className="text-lg font-semibold text-cosmic-txt-1">
                      {dev.name}
                    </h3>
                    <p className="text-sm text-cosmic-txt-2">
                      {dev.role}
                    </p>
                  </div>

                  <p className="text-xs text-cosmic-muted leading-relaxed">
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>
      </main>

      <footer className="border-t border-cosmic-border/40 bg-cosmic-bg-2/80 backdrop-blur-md">
        <div className="container mx-auto px-6 py-8 sm:py-10">
          <div className="flex flex-col gap-8 sm:flex-row sm:items-start sm:justify-between">
            <div className="space-y-3 max-w-sm">
              <h3 className="text-lg font-semibold text-cosmic-txt-1">
                AWS Cloud Health Dashboard
              </h3>
              <p className="text-sm text-cosmic-txt-2 leading-relaxed">
                Monitor, optimize, and secure your AWS workloads with a modern,
                cosmic-inspired observability experience.
              </p>
            </div>

            <div className="flex flex-wrap gap-8 text-sm">
              <div className="space-y-2">
                <p className="text-xs font-semibold tracking-[0.25em] text-cosmic-muted uppercase">
                  Services
                </p>
                <ul className="space-y-1.5 text-cosmic-txt-2">
                  <li className="hover:text-cosmic-accent cursor-pointer">Dashboard</li>
                  <li className="hover:text-cosmic-accent cursor-pointer">Cost Explorer</li>
                  <li className="hover:text-cosmic-accent cursor-pointer">S3 Buckets</li>
                  <li className="hover:text-cosmic-accent cursor-pointer">Architecture</li>
                </ul>
              </div>

              <div className="space-y-2">
                <p className="text-xs font-semibold tracking-[0.25em] text-cosmic-muted uppercase">
                  Contact
                </p>
                <p className="text-cosmic-txt-2">
                  Phone: 0123456789<br />
                  
                </p>
                <p className="text-cosmic-muted text-xs">
                  Email: cloud-health@university.demo
                </p>
              </div>
            </div>
          </div>

          <div className="mt-8 pt-4 border-t border-cosmic-border/40 flex flex-col sm:flex-row items-center justify-between gap-3">
            <p className="text-xs text-cosmic-muted">
              © {new Date().getFullYear()} AWS Cloud Health Dashboard. All rights reserved.
            </p>
            <p className="text-xs text-cosmic-muted">
              Crafted with care by the Cloud Health Dev Team.
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Home;