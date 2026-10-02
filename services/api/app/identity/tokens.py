"""OIDC verification; provider claims are proof, application capabilities are separate."""
import jwt


def validate_token(token: str, public_key, issuer: str, audiences: list[str]) -> dict:
    try:
        claims = jwt.decode(token, public_key, algorithms=['RS256'], issuer=issuer,
                            audience=audiences, options={'require':['iss','sub','aud','exp','iat']})
    except jwt.PyJWTError as exc:
        raise ValueError('Invalid or expired identity proof') from exc
    if not claims.get('sub') or claims.get('email_verified') is not True:
        raise ValueError('Verified account is required')
    return claims
