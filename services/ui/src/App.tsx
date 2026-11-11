import {lazy, Suspense} from "react";
const LegacyApp=lazy(()=>import("./LegacyApp"));
const Product=lazy(()=>import("./product/Product"));
export default function App(){return <Suspense fallback={<div role="status">Loading Housing Insights…</div>}>{import.meta.env.VITE_HOUSING_V2==="false"?<LegacyApp/>:<Product/>}</Suspense>}
