import Image from "next/image";
import mark from "./hinaing-mark.png";

type HinaingLogoProps = {
  className?: string;
  alt?: string;
  priority?: boolean;
};

export function HinaingLogo({ className, alt = "Hinaing", priority = false }: HinaingLogoProps) {
  return (
    <Image
      src={mark}
      alt={alt}
      priority={priority}
      draggable={false}
      sizes="80px"
      className={className}
    />
  );
}
