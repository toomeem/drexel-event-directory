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

export function AboutPage() {
    return (
        <div className="about-page">
            <h1 className="about-page__title">About Drexel Event Hub</h1>
            <p className="about-page__body">
                Drexel Event Hub is a centralized directory of events happening on and
                around Drexel University's campus. Instead of checking multiple sites,
                you can browse, filter, and search for everything in one place, including
                club meetings, academic lectures, athletics games, and cultural
                celebrations.
            </p>

            <section className="about-page__section">
                <h2 className="about-page__section-title">Features</h2>
                <ul className="about-page__feature-list">
                    <li>Filter by date range, event format (in-person, virtual, hybrid), theme, and perks</li>
                    <li>Search across event names and organizers</li>
                    <li>Ask the built-in assistant questions about upcoming events</li>
                    <li>Events refresh automatically so listings stay current</li>
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
                                {source.name} ↗
                            </a>
                            <p className="about-page__source-desc">{source.description}</p>
                        </li>
                    ))}
                </ul>
            </section>

            <div className="about-page__row">
                <section className="about-page__section">
                    <h2 className="about-page__section-title">For Recruiters😁</h2>
                    <p className="about-page__body">
                        Interested in my work?{" "}
                        <a
                            href="https://drexel-events-general-bucket-034584778101-us-east-1-an.s3.us-east-1.amazonaws.com/resume_V3.pdf"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="about-page__source-name"
                        >
                            View my resume ↗
                        </a>
                    </p>
                </section>

                <section className="about-page__section">
                    <h2 className="about-page__section-title">Open Source</h2>
                    <p className="about-page__body">

                        <a
                            href="https://github.com/toomeem/drexel-event-directory/"
                            target="_blank"
                            rel="noopener noreferrer"
                            className="about-page__source-name"
                        >
                            View the source on GitHub ↗
                        </a>
                    </p>
                </section>
            </div>
        </div>
    );
}
