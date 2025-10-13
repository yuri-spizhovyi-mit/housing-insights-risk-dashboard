function Footer() {
  return (
    <footer className="px-8 pt-8 pb-16">
      <p className="text-primary">
        &copy;Copyright by Housing Insights & Risk Forecast at{" "}
        {new Date().getFullYear()}
      </p>
    </footer>
  );
}

export default Footer;
