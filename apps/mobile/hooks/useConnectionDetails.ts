import { useEffect, useState } from "react";

// Production token server configuration
const API_URL = process.env.EXPO_PUBLIC_API_URL || "http://localhost:3000";
const tokenEndpoint = `${API_URL}/api/token`;

// For use without a token server.
const hardcodedUrl = "";
const hardcodedToken = "";

/**
 * Retrieves a LiveKit token from the Joyce production server.
 */
export function useConnectionDetails(): ConnectionDetails | undefined {
	const [details, setDetails] = useState<ConnectionDetails | undefined>(() => {
		return undefined;
	});

	useEffect(() => {
		fetchToken().then((details) => {
			setDetails(details);
		});
	}, []);

	return details;
}

export async function fetchToken(): Promise<ConnectionDetails | undefined> {
	// Fallback to hardcoded values if configured
	if (hardcodedUrl && hardcodedToken) {
		return {
			url: hardcodedUrl,
			token: hardcodedToken,
		};
	}

	try {
		const response = await fetch(tokenEndpoint, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
			},
			body: JSON.stringify({
				room_name: "joyce-room",
				participant_name: "mobile-user",
			}),
		});

		if (!response.ok) {
			throw new Error(`HTTP error! status: ${response.status}`);
		}

		const json = await response.json();

		if (json.serverUrl && json.participantToken) {
			return {
				url: json.serverUrl,
				token: json.participantToken,
			};
		} else {
			return undefined;
		}
	} catch (error) {
		console.error("Failed to fetch token from server:", error);
		return undefined;
	}
}

export type ConnectionDetails = {
	url: string;
	token: string;
};
