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
    {
        name: "Black Bottom Jazz 🎷",
        url: "https://blackbottomjazz.org/",
        description:
            "The Black Bottom Lives On! jazz series, bringing recurring live jazz performances and cultural programming to the neighborhood.",
    },
];

const FEATURES = [
    "Filter by date range, event format, event type, and perks",
    "Search across event names, organizers, and descriptions",
    "Browse listings from multiple campus and neighborhood sources",
    "Ask the built-in assistant questions about upcoming events",
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
                    Event data is collected from seven campus and neighborhood
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

                <a
                    href="https://github.com/toomeem/drexel-event-directory/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="about-page__source-name"
                >
                    View the code on GitHub
                    <span aria-hidden="true"> -&gt;</span>
                </a>
            </div>
        </div>
    );
}
