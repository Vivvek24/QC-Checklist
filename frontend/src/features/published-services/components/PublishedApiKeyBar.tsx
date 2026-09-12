/**
 * Page-level API key bar for the Published Services test harness.
 *
 * The published endpoints accept an optional shared secret via the `X-API-Key`
 * header. When the corresponding backend setting is empty the endpoints are
 * open, so this field can be left blank. When a key is entered it is sent with
 * every call made from the page.
 */

import { Card } from 'primereact/card';
import { Password } from 'primereact/password';

interface PublishedApiKeyBarProps {
  apiKey: string;
  onChange: (value: string) => void;
}

export const PublishedApiKeyBar = ({ apiKey, onChange }: PublishedApiKeyBarProps) => {
  return (
    <Card className="mb-3">
      <div className="grid align-items-center">
        <div className="col-12 md:col-4">
          <label htmlFor="published-api-key" className="block font-medium mb-1">
            X-API-Key <span className="text-500 font-normal">(optional)</span>
          </label>
          <span className="text-600 text-sm">
            Leave empty when the published endpoints are open (no key configured).
          </span>
        </div>
        <div className="col-12 md:col-8">
          <Password
            inputId="published-api-key"
            value={apiKey}
            onChange={(e) => onChange(e.target.value)}
            feedback={false}
            toggleMask
            placeholder="Sent as the X-API-Key header on every request"
            className="w-full"
            inputClassName="w-full"
          />
        </div>
      </div>
    </Card>
  );
};
