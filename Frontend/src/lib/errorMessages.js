export const getUserFriendlyErrorMessage = (error, fallbackMessage) => {
  if (!error) return fallbackMessage || "Something went wrong. Please try again.";

  const status = error.response?.status;
  const serverError =
    error.response?.data?.error ||
    error.response?.data?.message ||
    error.message;

  if (status === 401) {
    return "Your session has expired. Please login again.";
  }

  if (status === 403) {
    return "You do not have permission to perform this action.";
  }

  if (status === 404) {
    return "The requested record was not found. Please refresh and try again.";
  }

  if (status === 409) {
    return (
      serverError ||
      "A duplicate record already exists. Please update the existing one."
    );
  }

  if (status === 422 || status === 400) {
    return (
      serverError ||
      "Some input values are invalid. Please review the form and try again."
    );
  }

  if (error.code === "ECONNABORTED") {
    return "The request is taking longer than expected. Please wait and try again.";
  }

  if (error.message?.toLowerCase().includes("network")) {
    return "Unable to reach server. Check your connection and server status.";
  }

  return serverError || fallbackMessage || "Something went wrong. Please try again.";
};
