const SOURCES = [
    {
        name: "Drexel Events 🗓️",
        url: "https://drexel.edu/events?q&sortBy=relevance&sortOrder=asc&page=1&startDate&endDate",
        description:
            "The official Drexel University events calendar, covering academic talks, workshops, career fairs, cultural programs, and university-wide happenings.",
    },
    {
        name: "DragonLink 🐉",
        url: "https://drexel.campuslabs.com/engage/",
        description:
            "Drexel's student engagement platform, where registered student organizations post club meetings, social events, fundraisers, and more.",
    },
    {
        name: "Drexel Athletics 🏀",
        url: "https://drexeldragons.com/",
        description:
            "The official home of Drexel Dragons athletics, providing schedules for all varsity sports including basketball, soccer, lacrosse, swimming, and more.",
    },
    {
        name: "uCity Lawn 🌳",
        url: "https://ucitysquare.com/events/month/",
        description:
            "uCity Square's event calendar for The Lawn and nearby public programming, including yoga sessions, concerts, and community events.",
    },
    {
        name: "University City District 🏙️",
        url: "https://www.universitycity.org/events",
        description:
            "University City District's neighborhood calendar, covering public programming, workshops, live music, and community happenings.",
    },
    {
        name: "Local Restaurants 🎲",
        url: "https://www.thepostphl.com/",
        description:
            "Weekly recurring events at nearby spots like The Post at Cira Garage, Sunset Social, and Gather Food Hall, including music bingo, quizzo, game nights, and movie nights.",
    },
];

const FEATURES = [
    "Filter by date range, event format, event type, and perks",
    "Search across event names, organizers, and descriptions",
    "Browse listings from multiple campus and neighborhood sources",
    "Ask the built-in assistant questions about upcoming events",
];

const CONTACTS = [
    {
        label: "emt324@drexel.edu",
        url: "mailto:emt324@drexel.edu",
        external: false,
        icon: <EmailIcon/>,
    },
    {
        label: "Connect on LinkedIn",
        url: "https://www.linkedin.com/in/evan-toomey-a0b91",
        external: true,
        icon: <LinkedInIcon/>,
    },
    {
        label: "View the code on GitHub",
        url: "https://github.com/toomeem/drexel-event-directory/",
        external: true,
        icon: <GitHubIcon/>,
    },
];

export function AboutPage() {
    return (
        <div className="about-page">
            <header className="about-page__hero">
                <h1 className="about-page__title">The one-stop shop for campus events.</h1>
            </header>
            <section className="about-page__section">
                <h2 className="about-page__section-title">Features</h2>
                <ul className="about-page__feature-list">
                    {FEATURES.map((feature) => (
                        <li key={feature}>{feature}</li>
                    ))}
                </ul>
            </section>

            <section className="about-page__section">
                <h2 className="about-page__section-title">Sources of Events</h2>
                <p className="about-page__body">
                    Event data is collected from six campus and neighborhood
                    sources
                </p>
                <ul className="about-page__source-list">
                    {SOURCES.map((source) => (
                        <li key={source.name} className="about-page__source-item">
                            <a
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="about-page__source-link"
                            >
                                <span className="about-page__source-name">
                                    {source.name}
                                </span>
                                <span className="about-page__source-desc">
                                    {source.description}
                                </span>
                            </a>
                        </li>
                    ))}
                </ul>
            </section>

            <div className="about-page__row">
                {/* <section className="about-page__section">
                    <div className="about-page__section-header">
                        <h2 className="about-page__section-title">For Recruiters 😁</h2>
                        <a
                            href="https://drexel-events-general-bucket-034584778101-us-east-1-an.s3.us-east-1.amazonaws.com/resume_V3.pdf"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="about-page__source-name"
                        >
                            View my resume
                            <span aria-hidden="true"> -&gt;</span>
                        </a>
                    </div>
                    <p className="about-page__body">
                        A full-stack project with a Python data pipeline, a
                        SQL database, served through a React and
                        TypeScript frontend, and hosted on AWS infrastructure (Lambda, S3,
                        RDS, Bedrock, CloudFront).
                    </p>
                </section> */}

                <section className="about-page__section">
                    <ul className="about-page__contact-list">
                        {CONTACTS.map((contact) => (
                            <li key={contact.url}>
                                <a
                                    href={contact.url}
                                    target={contact.external ? "_blank" : undefined}
                                    rel={contact.external ? "noopener noreferrer" : undefined}
                                    className="about-page__source-name about-page__contact-link"
                                >
                                    {contact.icon}
                                    {contact.label}
                                    <span aria-hidden="true"> -&gt;</span>
                                </a>
                            </li>
                        ))}
                    </ul>
                </section>
            </div>
        </div>
    );
}

function EmailIcon() {
    return (
        <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            <rect x="2" y="4" width="20" height="16" rx="2"/>
            <polyline points="22,6 12,13 2,6"/>
        </svg>
    );
}

function LinkedInIcon() {
    return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path
                d="M20.45 20.45h-3.56v-5.57c0-1.33-.02-3.04-1.85-3.04-1.85 0-2.14 1.45-2.14 2.94v5.67H9.34V9h3.42v1.56h.05c.48-.9 1.64-1.85 3.37-1.85 3.6 0 4.27 2.37 4.27 5.46v6.28zM5.34 7.43a2.06 2.06 0 1 1 0-4.13 2.06 2.06 0 0 1 0 4.13zM7.12 20.45H3.56V9h3.56v11.45zM22.22 0H1.77C.79 0 0 .77 0 1.73v20.54C0 23.23.79 24 1.77 24h20.45c.98 0 1.78-.77 1.78-1.73V1.73C24 .77 23.2 0 22.22 0z"/>
        </svg>
    );
}

function GitHubIcon() {
    return (
        <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
            <path
                d="M12 .3a12 12 0 0 0-3.8 23.38c.6.12.83-.26.83-.57v-2c-3.34.73-4.04-1.6-4.04-1.6-.55-1.4-1.34-1.77-1.34-1.77-1.08-.74.09-.73.09-.73 1.2.09 1.83 1.24 1.83 1.24 1.07 1.83 2.8 1.3 3.49 1 .1-.78.42-1.3.76-1.6-2.67-.3-5.47-1.33-5.47-5.93 0-1.31.47-2.38 1.24-3.22-.13-.3-.54-1.52.12-3.18 0 0 1-.32 3.3 1.23a11.5 11.5 0 0 1 6 0c2.28-1.55 3.29-1.23 3.29-1.23.66 1.66.24 2.88.12 3.18.77.84 1.24 1.91 1.24 3.22 0 4.61-2.8 5.63-5.48 5.92.43.37.81 1.1.81 2.22v3.29c0 .32.22.7.83.57A12 12 0 0 0 12 .3z"/>
        </svg>
    );
}
