import Link from "next/link";
import Image from "next/image";

import "bootstrap/dist/css/bootstrap.min.css";
import { Button } from "react-bootstrap";

export function ExpandButton({ to }: { to: string }) {
  return (
    <Link href={to} className="text-white text-decoration-none">
      <Button>
        <Image
          src="/icons/expand_icon.svg"
          alt="expand-icon"
          width={25}
          height={25}
        />
      </Button>
    </Link>
  );
}

export function BackButton() {
  return (
    <Link href="/">
      <Button variant="secondary">
        <Image
          src="/icons/back_icon.svg"
          alt="back-icon"
          width={25}
          height={25}
        />
      </Button>
    </Link>
  );
}
