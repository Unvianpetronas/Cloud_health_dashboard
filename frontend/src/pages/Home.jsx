import React from 'react';
import { useNavigate } from 'react-router-dom';

import Header from '../components/common/Header';
import { useAuth } from '../contexts/AuthContext';

const Home = () => {
  const { user } = useAuth();
  const navigate = useNavigate();

  return (
    <div className="min-h-screen">
      <Header
        title="AWS Cloud Health Dashboard"
        showNavigation={true}
      />

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
      <section className="container mx-auto px-6 mt-[140px] sm:mt-[160px] pb-20">
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
            { name: 'Developer 1', role: 'Cloud / Backend Engineer' },
            { name: 'Developer 2', role: 'Frontend / UI Engineer' },
            { name: 'Developer 3', role: 'DevOps / Infrastructure' },
            { name: 'Developer 4', role: 'QA / Automation Engineer' },
          ].map((dev, idx) => (
            <div
              key={idx}
              className="w-full max-w-xs bg-cosmic-card border border-cosmic-border/60 rounded-2xl p-6 shadow-cosmic-soft hover:shadow-cosmic-glow transition-transform duration-200 hover:-translate-y-1 backdrop-blur-md"
            >
              <div className="flex flex-col items-center text-center space-y-4">
                {/* Avatar placeholder – bạn có thể thay bằng <img src="..."> sau này */}
                <div className="w-20 h-20 rounded-2xl bg-gradient-to-br from-blue-500 via-indigo-500 to-purple-500 flex items-center justify-center shadow-lg shadow-blue-500/40">
                  <span className="text-2xl font-semibold text-white">
                    {dev.name.charAt(0)}
                  </span>
                </div>

                <div>
                  <h3 className="text-lg font-semibold text-cosmic-txt-1">
                    {dev.name}
                  </h3>
                  <p className="text-sm text-cosmic-txt-2">
                    {dev.role}
                  </p>
                </div>

                <p className="text-xs text-cosmic-muted leading-relaxed">
                  Replace this text with a short bio or responsibilities for each
                  member, such as AWS services handled, features implemented, or
                  favorite cloud tools.
                </p>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};

export default Home;