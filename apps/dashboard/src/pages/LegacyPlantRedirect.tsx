import { Navigate, useParams } from "react-router-dom";
export default function LegacyPlantRedirect() {
  const { plantId } = useParams();
  return (
    <Navigate
      to={`/dashboard/plants/${encodeURIComponent(plantId ?? "")}`}
      replace
    />
  );
}
