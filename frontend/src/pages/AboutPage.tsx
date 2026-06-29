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
];

const FEATURES = [
    "Filter by date range, event format, event type, and perks",
    "Search across event names, organizers, and descriptions",
    "Ask the built-in assistant questions about upcoming events",
    "Browse deduplicated listings from multiple official Drexel sources",
];

export function AboutPage() {
    return (
        <div className="about-page">
            <header className="about-page__hero">
                <p className="about-page__eyebrow">Drexel Event Hub</p>
                <h1 className="about-page__title">One place to find campus events.</h1>
                <p className="about-page__body about-page__intro">
                    Drexel Event Hub brings together events happening on and around Drexel
                    University's campus. Instead of checking several sites, you can browse,
                    filter, and search for club meetings, academic lectures, athletics
                    games, career events, and cultural programs from a single directory.
                </p>
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
                <h2 className="about-page__section-title">Data Sources</h2>
                <p className="about-page__body">
                    Event data is collected from three official Drexel sources and
                    deduplicated automatically.
                </p>
                <ul className="about-page__source-list">
                    {SOURCES.map((source) => (
                        <li key={source.name} className="about-page__source-item">
                            <a
                                href={source.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="about-page__source-name"
                            >
                                {source.name}
                            </a>
                            <p className="about-page__source-desc">{source.description}</p>
                        </li>
                    ))}
                </ul>
            </section>

            <div className="about-page__row">
                <section className="about-page__section">
                    <h2 className="about-page__section-title">For Recruiters 😁</h2>
                    <p className="about-page__body">
                        This project highlights React, TypeScript, API integration,
                        filtering, responsive UI, and deployment work.\n{" "}
                        <a
                            href="https://drexel-events-general-bucket-034584778101-us-east-1-an.s3.us-east-1.amazonaws.com/resume_V3.pdf"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="about-page__source-name"
                        >
                            View my resume
                            <span aria-hidden="true"> -&gt;</span>
                        </a>
                    </p>
                </section>

                <section className="about-page__section">
                    <h2 className="about-page__section-title">Open Source</h2>
                    <p className="about-page__body">
                        The frontend and related project code are available on GitHub for
                        review.{" "}
                        <a
                            href="https://github.com/toomeem/drexel-event-directory/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="about-page__source-name"
                        >
                            View the source on GitHub
                            <span aria-hidden="true"> -&gt;</span>
                        </a>
                    </p>
                </section>
            </div>
        </div>
    );
}
