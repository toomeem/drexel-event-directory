const SOURCES = [
  {
    name: "Drexel Events",
    url: "https://drexel.edu/events?q&sortBy=relevance&sortOrder=asc&page=1&startDate&endDate",
    description:
      "The official Drexel University events calendar, covering academic talks, workshops, career fairs, cultural programs, and university-wide happenings.",
  },
  {
    name: "DragonLink",
    url: "https://drexel.campuslabs.com/engage/",
    description:
      "Drexel's student engagement platform, where registered student organizations post club meetings, social events, fundraisers, and more.",
  },
  {
    name: "Drexel Athletics",
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
        you can browse, filter, and search everything in one place — from club
        meetings and academic lectures to athletics games and cultural
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
          deduplicated automatically when the same event appears in more than one.
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
    </div>
  );
}
