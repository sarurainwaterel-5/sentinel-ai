function ListSection({
  title,
  items = [],
}) {
  if (!items.length) {
    return null;
  }

  return (
    <section>
      <p className="eyebrow">
        {title}
      </p>

      <ul>
        {items.map((item, index) => (
          <li key={index}>
            {item}
          </li>
        ))}
      </ul>
    </section>
  );
}


export default function ReasonLimitations({
  limitations = [],
  alternatives = [],
  missingInformation = [],
}) {
  if (
    !limitations.length &&
    !alternatives.length &&
    !missingInformation.length
  ) {
    return null;
  }

  return (
    <article className="panel reason-limitations">
      <ListSection
        title="Limitations"
        items={limitations}
      />

      <ListSection
        title="Alternative Interpretations"
        items={alternatives}
      />

      <ListSection
        title="Missing Information"
        items={missingInformation}
      />
    </article>
  );
}
